from app.services.scoring import score_lead

def test_score_lead_alta():
    
    #Arrange (creacion lead)
    lead = {
        "id": 1,
        "nombre": "Juaniko",
        "empresa": "DataQuant",
        "email": "Email@email.com",
        "sector": "Administracion",
        "ingresos_estimados": 6_000_000,
        "empleados": 550,
        "ultimo_contacto_dias": 130,
        "interes": 10
    }

    #Act(ejecutamos funcion)
    result = score_lead(lead)

    #assert (comprobamos)
    assert result["score"] >= 70
    assert result["prioridad"] == "alta"
    assert "razones" in result and isinstance(result["razones"], list)
    assert len(result["razones"]) > 0


def test_score_lead_media():

    #Arrange (creacion lead)   
    lead = {
        "id": 2,
        "nombre": "Pepin",
        "empresa": "DataQuant",
        "email": "Email@email.com",
        "sector": "Administracion",
        "ingresos_estimados": 1_500_000,
        "empleados": 250,
        "ultimo_contacto_dias": 70,
        "interes": 6
    }

    #Act(ejecutamos funcion)
    result = score_lead(lead)

    #assert (comprobamos)
    assert result["prioridad"] == "media"
    assert 40 <= result["score"] < 70
    assert "razones" in result and isinstance(result["razones"], list)
    assert len(result["razones"]) > 0

def test_score_lead_baja():

    #Arrange (creacion lead)
    lead = {
        "id": 3,
        "nombre": "Pepin",
        "empresa": "DataQuant",
        "email": "Email@email.com",
        "sector": "Administracion",
        "ingresos_estimados": 20_000,
        "empleados": 11,
        "ultimo_contacto_dias": 4,
        "interes": 2
    }
    #Act(ejecutamos funcion)
    result = score_lead(lead)

    #assert (comprobamos)
    assert result["prioridad"] == "baja"
    assert result["score"] < 40
    assert "razones" in result and isinstance(result["razones"], list)
