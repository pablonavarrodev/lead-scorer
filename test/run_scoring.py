from app.services.storage import read_leads_csv
from app.services.scoring import score_all

leads = read_leads_csv("data/leads.csv")

# Aplicar scoring
scored_leads = score_all(leads)

# Mostrar primeros 3
print("\n--- Primeros 3 leads puntuados ---")
for lead in scored_leads[:3]:
    print(lead["nombre"], "| Score:", lead["score"], "| Prioridad:", lead["prioridad"])

# Ordenar por score descendente
# lo de key es para indicar en funcion de que lo ordena y lambda indica que es una funcion que devuelve score
sorted_leads = sorted(scored_leads, key=lambda x: x["score"], reverse=True)

print("\n--- TOP 3 por score ---")
for lead in sorted_leads[:3]:
    print(lead["nombre"], "| Score:", lead["score"], "| Prioridad:", lead["prioridad"])

# 5. Ver razones del mejor
best = sorted_leads[0]
print("\n--- Razones del mejor lead ---")
print(best["nombre"])
for r in best["razones"]:
    print("-", r)