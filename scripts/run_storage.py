from app.services.storage import read_leads_csv

leads = read_leads_csv("data/leads.csv")

print("Cantidad de leads: ",len(leads))
print("Primer lead: ",leads[0])
print("Tipo de id:", (leads[0]["id"]))
print("Tipo de ingresos:", (leads[0]["ingresos_estimados"]))
print("Tipo de interes:", (leads[0]["interes"]))