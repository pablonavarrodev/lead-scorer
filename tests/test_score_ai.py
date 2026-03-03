from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

#se mockea la respuesta del llm porque github no tiene la api key y asi no dependemos de apis externas en test

def test_score_ai_returns_rule_score_and_ai_block(monkeypatch):
    #función falsa para sustituir a enrich_lead_ai (de la api)
    def fake_enrich_lead_ai(*args, **kwargs): #los argumentos no importan porque no se usan asi que ponemos eso para recogerlos y que sea igual
        #devuelve un LeadAIResult
        return {
            "ai_summary": "Lead con buen encaje: interés alto y contacto reciente.",
            "risk_flags": [],
            "next_action": "call",
            "reasoning_short": "El interés es alto y el contacto es reciente, por eso conviene llamar."
        }

    #ahora cambiamos la función real por la falsa
    import app.api.routes as routes
    monkeypatch.setattr(routes, "enrich_lead_ai", fake_enrich_lead_ai)

    #creamos lead de prueba
    payload = {
        "id": 1,
        "nombre": "Carlos López",
        "empresa": "NovaTech Solutions",
        "email": "carlos@novatech.example.com",
        "sector": "Tecnología",
        "ingresos_estimados": 2500000,
        "empleados": 45,
        "ultimo_contacto_dias": 12,
        "interes": 8
    }

    r = client.post("/score-ai", json=payload)

    assert r.status_code == 200

    data = r.json()

    # Comprueba que rule_score existe y es int
    assert "rule_score" in data
    assert isinstance(data["rule_score"], int)

    # Comprueba que ai existe
    assert "ai" in data
    ai = data["ai"]

    # Comprueba campos del bloque ai
    assert "ai_summary" in ai
    assert "risk_flags" in ai
    assert "next_action" in ai
    assert "reasoning_short" in ai

    # next_action debe ser una de las permitidas
    assert ai["next_action"] in ["call", "email", "validate_data", "discard"]