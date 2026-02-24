
sectores_saturados = {"Marketing", "Retail", "Construcción"}

def score_lead(lead):

    score = 0
    razones = []

    if lead["interes"] >= 9: 
        score += 30
        razones.append("Interes muy alto >= 9")
    elif lead["interes"] >= 8:
        score += 25
        razones.append("Interes alto >= 8")
    elif lead["interes"] >= 6:
        score += 15
        razones.append("Interes medio >= 6")
    elif lead["interes"] >= 4:
        score += 5
        razones.append("Interes normal >= 4")

    if lead["ingresos_estimados"] > 5_000_000: 
        score += 25
        razones.append("Ingresos > 5M")
    elif lead["ingresos_estimados"] > 2_000_000:
        score += 20
        razones.append("Ingresos > 2M")
    elif lead["ingresos_estimados"] > 1_000_000:
        score += 15
        razones.append("Ingresos > 1M")
    elif lead["ingresos_estimados"] > 500_000:
        score += 5
        razones.append("Ingresos > 500k")

    if lead["ultimo_contacto_dias"] >= 120:
        score += 20
        razones.append("Lead frío (>120 días)")
    elif lead["ultimo_contacto_dias"] >= 90:
        score += 15
        razones.append("Lead frío (>90 días)")
    elif lead["ultimo_contacto_dias"] >= 60:
        score += 10
        razones.append("Lead frío (>60 días)")
    elif lead["ultimo_contacto_dias"] >= 30:
        score += 5
        razones.append("Lead frío (>30 días)")

    if lead["empleados"] >= 500:
        score += 15
        razones.append("+500 empleados")
    elif lead["empleados"] >= 200:
        score += 10
        razones.append("+200 empleados")
    elif lead["empleados"] >= 50:
        score += 5
        razones.append("+50 empleados")

    if lead["sector"] in sectores_saturados:
        score -= 10
        razones.append("Sector saturado (-10)")

    if score >= 70:
        prioridad = "alta"
    elif score >= 40:
        prioridad = "media"
    else:
        prioridad = "baja"

    new_lead = {
        "id": lead["id"],
        "nombre": lead["nombre"],
        "empresa": lead["empresa"],
        "email": lead["email"],
        "sector": lead["sector"],
        "ingresos_estimados": lead["ingresos_estimados"],
        "empleados": lead["empleados"],
        "ultimo_contacto_dias": lead["ultimo_contacto_dias"],
        "interes": lead["interes"],
        "score": score,
        "prioridad": prioridad,
        "razones": razones,
    }

    return new_lead


def score_all(leads):

    new_leads = []

    for lead in leads:
        new_leads.append(score_lead(lead))

    return new_leads