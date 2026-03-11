from fastapi.testclient import TestClient

from app.main import app
from app.schemas import LeadAIResult, EnrichedLead

client = TestClient(app)


class FakeCSVPath:
    def exists(self):
        return True

    def __str__(self):
        return "fake_leads.csv"


class FakeOutputDir:
    def mkdir(self, exist_ok=False):
        return None


class FakeOutputFile:
    def __str__(self):
        return "output/leads_enriched.json"


def test_post_enrich_all_run_returns_200_and_expected_payload(monkeypatch):
    """
    Comprueba que el endpoint POST /enrich-all/run:
    - responde 200
    - llama al pipeline
    - devuelve el JSON esperado
    """

    fake_leads = [
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
        }
    ]

    fake_enriched = [
        EnrichedLead(
            lead=fake_leads[0],
            rule_score=78,
            prioridad="alta",
            razones=["Interés alto"],
            ai=LeadAIResult(
                ai_summary="Lead prometedor",
                risk_flags=[],
                next_action="call",
                reasoning_short="Buen encaje comercial"
            )
        )
    ]

    # Simulamos dependencias externas del endpoint
    monkeypatch.setattr("app.api.routes.DATA_CSV", FakeCSVPath())
    monkeypatch.setattr("app.api.routes.OUTPUT_DIR", FakeOutputDir())
    monkeypatch.setattr("app.api.routes.OUTPUT_ENRICH_JSON", FakeOutputFile())
    monkeypatch.setattr("app.api.routes.read_leads_csv", lambda path: fake_leads)
    monkeypatch.setattr("app.api.routes.enrich_all_ai", lambda leads, mode: (fake_enriched, 0))
    monkeypatch.setattr("app.api.routes.save_enriched_lead", lambda enriched, status="ok": None)
    monkeypatch.setattr("app.api.routes.write_json", lambda data, path: None)

    r = client.post("/enrich-all/run?mode=overwrite")

    assert r.status_code == 200

    data = r.json()
    assert data["status"] == "ok"
    assert data["total"] == 1
    assert data["enriched"] == 1
    assert data["skipped"] == 0
    assert "output_file" in data


def test_get_db_enriched_leads_returns_list(monkeypatch):
    """
    Comprueba que GET /db/leads/enriched devuelve una lista JSON.
    """

    fake_data = [
        {
            "id": 1,
            "nombre": "Carlos",
            "empresa": "NovaTech",
            "sector": "Tecnología",
            "score": 78,
            "interes": 8,
            "status": "ok",
            "created_at": "2026-03-06 10:00:00",
            "updated_at": "2026-03-06 10:00:00",
            "enriched": {
                "lead": {
                    "id": 1,
                    "nombre": "Carlos",
                    "empresa": "NovaTech",
                    "email": "carlos@novatech.com",
                    "sector": "Tecnología",
                    "ingresos_estimados": 2_500_000,
                    "empleados": 45,
                    "ultimo_contacto_dias": 12,
                    "interes": 8
                },
                "rule_score": 78,
                "prioridad": "alta",
                "razones": ["Interés alto"],
                "ai": {
                    "ai_summary": "Lead prometedor",
                    "risk_flags": [],
                    "next_action": "call",
                    "reasoning_short": "Buen encaje comercial"
                }
            }
        }
    ]

    monkeypatch.setattr("app.api.routes.get_leads_enriched", lambda: fake_data)

    r = client.get("/db/leads/enriched")

    assert r.status_code == 200
    data = r.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["nombre"] == "Carlos"
    assert data[0]["score"] == 78
    assert data[0]["status"] == "ok"


def test_get_db_enriched_lead_by_id_returns_404_if_missing(monkeypatch):
    """
    Comprueba que GET /db/leads/enriched/{id} devuelve 404
    cuando el lead no existe en la BD.
    """

    monkeypatch.setattr("app.api.routes.get_enriched_lead_by_id", lambda lead_id: None)

    r = client.get("/db/leads/enriched/999")

    assert r.status_code == 404
    data = r.json()
    assert "detail" in data
    assert "no existe en la BD" in data["detail"]