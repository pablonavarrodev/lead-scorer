from types import SimpleNamespace

from app.schemas import LeadAIResult, EnrichedLead
from app.services.llm_enrichment import enrich_lead_ai, enrich_all_ai


# Comprueba que enrich_lead_ai transforma un JSON válido del LLM en LeadAIResult.
def test_enrich_lead_ai_returns_valid_object(monkeypatch):
    # Simulamos que sí hay API key para que no salte el RuntimeError
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Respuesta fake del LLM con un JSON válido
    valid_json = """
    {
        "ai_summary": "Lead prometedor con interés alto.",
        "risk_flags": [],
        "next_action": "call",
        "reasoning_short": "Interés alto y contacto reciente."
    }
    """

    # _get_llm() devuelve un objeto con método invoke(), así que lo imitamos
    class FakeLLM:
        def invoke(self, prompt):
            return SimpleNamespace(content=valid_json)

    # Sustituimos el LLM real por uno falso
    monkeypatch.setattr("app.services.llm_enrichment._get_llm", lambda: FakeLLM())

    lead = {
        "id": 1,
        "nombre": "Carlos",
        "empresa": "NovaTech",
        "email": "carlos@novatech.com",
        "sector": "Tecnología",
        "ingresos_estimados": 2_500_000,
        "empleados": 45,
        "ultimo_contacto_dias": 12,
        "interes": 8,
    }

    result = enrich_lead_ai(
        lead=lead,
        rule_score=78,
        prioridad="alta",
        razones_reglas=["Interés alto", "Contacto reciente"],
    )

    assert isinstance(result, LeadAIResult)
    assert result.ai_summary == "Lead prometedor con interés alto."
    assert result.next_action == "call"
    assert result.risk_flags == []
    assert "Interés alto" in result.reasoning_short


# Comprueba que si el primer intento devuelve JSON inválido,
# enrich_lead_ai reintenta y devuelve un LeadAIResult válido.
def test_enrich_lead_ai_retries_if_first_response_is_invalid(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    invalid_response = "esto no es json válido"

    valid_response = """
    {
        "ai_summary": "Lead con posible inconsistencia de datos.",
        "risk_flags": ["data_inconsistency"],
        "next_action": "validate_data",
        "reasoning_short": "Los datos parecen incoherentes y conviene revisarlos."
    }
    """

    # Este fake devuelve primero una respuesta mala y luego una buena
    class FakeLLM:
        def __init__(self):
            self.calls = 0

        def invoke(self, prompt):
            self.calls += 1
            if self.calls == 1:
                return SimpleNamespace(content=invalid_response)
            return SimpleNamespace(content=valid_response)

    fake_llm = FakeLLM()
    monkeypatch.setattr("app.services.llm_enrichment._get_llm", lambda: fake_llm)

    lead = {
        "id": 2,
        "nombre": "Ana",
        "empresa": "BigCorp",
        "email": "ana@bigcorp.com",
        "sector": "Retail",
        "ingresos_estimados": 9_000_000,
        "empleados": 2,
        "ultimo_contacto_dias": 5,
        "interes": 7,
    }

    result = enrich_lead_ai(
        lead=lead,
        rule_score=65,
        prioridad="media",
        razones_reglas=["Ingresos altos", "Pocos empleados"],
    )

    assert isinstance(result, LeadAIResult)
    assert result.next_action == "validate_data"
    assert "data_inconsistency" in result.risk_flags
    assert fake_llm.calls == 2


# Comprueba que enrich_all_ai, en modo skip, no vuelve a enriquecer
# un lead que ya existe en la BD.
def test_enrich_all_ai_skips_existing_leads_in_skip_mode(monkeypatch):
    leads = [
        {
            "id": 1,
            "nombre": "Carlos",
            "empresa": "NovaTech",
            "email": "carlos@novatech.com",
            "sector": "Tecnología",
            "ingresos_estimados": 2_500_000,
            "empleados": 45,
            "ultimo_contacto_dias": 12,
            "interes": 8,
        },
        {
            "id": 2,
            "nombre": "Lucía",
            "empresa": "MarketFlow",
            "email": "lucia@marketflow.com",
            "sector": "Retail",
            "ingresos_estimados": 1_200_000,
            "empleados": 30,
            "ultimo_contacto_dias": 40,
            "interes": 6,
        },
    ]

    # Score fake para no depender aquí de la lógica real
    def fake_score_lead(lead):
        return {
            "score": 70,
            "prioridad": "alta",
            "razones": ["Score fake de prueba"]
        }

    # Resultado IA fake para no llamar al LLM real
    def fake_enrich_lead_ai(lead, rule_score, prioridad, razones_reglas):
        return LeadAIResult(
            ai_summary=f"Resumen IA para {lead['nombre']}",
            risk_flags=[],
            next_action="call",
            reasoning_short="Mock del enriquecimiento"
        )

    # El lead 1 ya existe en BD, el 2 no
    def fake_exist_enriched_lead(lead_id):
        return lead_id == 1

    monkeypatch.setattr("app.services.llm_enrichment.score_lead", fake_score_lead)
    monkeypatch.setattr("app.services.llm_enrichment.enrich_lead_ai", fake_enrich_lead_ai)
    monkeypatch.setattr("app.services.llm_enrichment.exist_enriched_lead", fake_exist_enriched_lead)

    enricheds, skipped = enrich_all_ai(leads, mode="skip")

    assert skipped == 1
    assert len(enricheds) == 1
    assert isinstance(enricheds[0], EnrichedLead)
    assert enricheds[0].lead.id == 2
    assert enricheds[0].ai.next_action == "call"