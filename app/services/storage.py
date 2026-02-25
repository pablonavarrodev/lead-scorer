import csv
import json

def read_leads_csv(path):

    leads = []

    #with es una estructura de control que me asegura que despues del open() va a aver un close() aunque se interrumpa la ejecucion
    with open(path, newline="", encoding="utf-8") as file:
        
        reader = csv.DictReader(file)

        for row in reader:
            lead = {
                "id": int(row["id"]),
                "nombre": row["nombre"].strip(),
                "empresa": row["empresa"].strip(),
                "email": row["email"].strip(),
                "sector": row["sector"].strip(),
                "ingresos_estimados": int(row["ingresos_estimados"]),
                "empleados": int(row["empleados"]),
                "ultimo_contacto_dias": int(row["ultimo_contacto_dias"]),
                "interes": int(row["interes"]),
            }

            leads.append(lead)

    return leads


def write_json(data, path):
    
    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            data, #Lista de leads
            file, #Archivo
            indent=2, #Formato legible
            ensure_ascii=False #Respeta tildes
        )