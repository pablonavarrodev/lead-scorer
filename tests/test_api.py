from typing import List

from fastapi.testclient import TestClient
from app.main import app

#creamos un cliente al que le mandamos nuestra api y este va a mandar las peticiones por nosotros
client = TestClient(app)

def test_health_returns_200():
    r = client.get("/health")
    assert r.status_code == 200

def test_post_score():
    payload = {
        "id": 1,
        "nombre": "Ana",
        "empresa": "BigCorp",
        "email": "ana@bigcorp.com",
        "sector": "Sanidad",
        "ingresos_estimados": 6_000_000,
        "empleados": 600,
        "ultimo_contacto_dias": 130,
        "interes": 10
    }

    r = client.post("/score", json=payload)
    assert r.status_code == 200

    data = r.json()
    assert "score" in data
    assert "prioridad" in data
    assert "razones" in data
    assert isinstance(data["razones"], list) #razones es una lista
    assert data["prioridad"] in {"alta", "media", "baja"}

def test_post_score_batch():
    payload = [
        {
        "id": 1,
        "nombre": "ana",
        "empresa": "metrodora",
        "email": "ana@bigcorp.com",
        "sector": "Sanidad",
        "ingresos_estimados": 6_000_000,
        "empleados": 600,
        "ultimo_contacto_dias": 130,
        "interes": 10
        },
        {
        "id": 2,
        "nombre": "Juaneta",
        "empresa": "indra",
        "email": "juaneta@indra.com",
        "sector": "Sanidad",
        "ingresos_estimados": 3_000_000,
        "empleados": 100,
        "ultimo_contacto_dias": 70,
        "interes": 10
        }
    ]

    r = client.post("/score/batch", json=payload)
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, List)
    assert len(data) == 2

    #aki mejor bucle por si son muchos leds
    assert "score" in data[0]
    assert "prioridad" in data[0]
    assert "razones" in data[0]
    assert "score" in data[1]
    assert "prioridad" in data[1]
    assert "razones" in data[1]

def test_post_score_invalid_422():
    payload = {
        "id": 1,
        "nombre": "Ana",
        "empresa": "BigCorp",
        "email": "ana@bigcorp.com",
        "sector": "Sanidad",
        "ingresos_estimados": 6_000_000,
        "empleados": 600,
        "ultimo_contacto_dias": 130,
        "interes": 11
    }

    r = client.post("/score", json=payload)
    assert r.status_code == 422