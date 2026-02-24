from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
from typing import List
from pathlib import Path
import json

from app.services.scoring import score_lead, score_all
from app.services.storage import read_leads_csv, write_json

app = FastAPI(title="Lead Scorer API")

#Rutas a los ficheros
BASE_DIR = Path(__file__).resolve().parents[1] #Saco la ruta de este archivo, la paso a absoluta, y subo 1 escalon a la ruta padre. file es main.py
DATA_CSV = BASE_DIR / "data" / "leads.csv"
OUTPUT_JSON = BASE_DIR / "output" / "leads_scored.json"
OUTPUT_DIR = BASE_DIR / "output"

# ---------
# MODELOS PYDANTIC: validan la entrada y salida de datos en los endpoints
# ---------

class LeadIn(BaseModel): #Hereda del modelo base (siempre)
    id: int
    nombre: str
    empresa: str
    email: EmailStr
    sector: str
    ingresos_estimados: int = Field(ge=0)    #ge: minimo  le: maximo
    empleados: int = Field(ge=0)
    ultimo_contacto_dias: int = Field(ge=0)
    interes: int = Field(ge=0, le=10)  


class LeadScored(LeadIn): #Hereda de LeadIn
    score: int
    prioridad: str
    razones: List[str]

# ---------
# Endpoints
# ---------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/score", response_model=LeadScored)
def score_one(lead: LeadIn):
    # lead.model_dump() convierte el modelo de pydantic a dict normal de Python
    return score_lead(lead.model_dump())


@app.post("/score/batch", response_model=List[LeadScored])
def score_batch(leads: List[LeadIn]):
    leads_dicts = [l.model_dump() for l in leads]
    return score_all(leads_dicts)


@app.get("/leads", response_model=List[LeadIn])
def get_leads_from_csv():
    if not DATA_CSV.exists():
        raise HTTPException(status_code=404, detail=f"No existe el CSV: {DATA_CSV}")
    return read_leads_csv(str(DATA_CSV))


@app.post("/pipeline/run")
def run_pipeline():
    if not DATA_CSV.exists():
        raise HTTPException(status_code=404, detail=f"No existe el CSV: {DATA_CSV}")

    OUTPUT_DIR.mkdir(exist_ok=True)

    leads = read_leads_csv(str(DATA_CSV))
    scored = score_all(leads)
    write_json(scored, str(OUTPUT_JSON))

    # nos cuenta cuantos hay de cada prioridad
    resumen = {"alta": 0, "media": 0, "baja": 0}
    for l in scored:
        resumen[l["prioridad"]] += 1

    return {
        "total": len(scored),
        "resumen_prioridad": resumen,
        "output_file": str(OUTPUT_JSON)
    }


@app.get("/leads/scored", response_model=List[LeadScored])
def get_scored_leads():
    if not OUTPUT_JSON.exists():
        raise HTTPException(
            status_code=404,
            detail="Aún no existe output/leads_scored.json. Ejecuta POST /pipeline/run primero."
        )

    with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data