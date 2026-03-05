from fastapi import APIRouter, HTTPException
from typing import List
import json
from app.schemas import LeadIn, LeadScored, LeadScoredAIResponse, EnrichedLead
from app.services.llm_enrichment import enrich_lead_ai, enrich_all_ai
from app.services.scoring import score_lead, score_all
from app.services.storage import read_leads_csv, write_json
from app.repositories.lead_repository import save_enriched_lead, get_leads_enriched, get_enriched_lead_by_id
from app.core.config import BASE_DIR, DATA_CSV, OUTPUT_DIR, OUTPUT_JSON, OUTPUT_ENRICH_JSON

#creamos el router que luego pasaremos a la app fastapi
router = APIRouter()

# ---------
# Endpoints
# ---------

@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/score", response_model=LeadScored)
def score_one(lead: LeadIn):
    # lead.model_dump() convierte el modelo de pydantic a dict normal de Python
    return score_lead(lead.model_dump())


@router.post("/score/batch", response_model=List[LeadScored])
def score_batch(leads: List[LeadIn]):
    leads_dicts = [l.model_dump() for l in leads]
    return score_all(leads_dicts)


@router.get("/leads", response_model=List[LeadIn])
def get_leads_from_csv():
    if not DATA_CSV.exists():
        raise HTTPException(status_code=404, detail=f"No existe el CSV: {DATA_CSV}")
    return read_leads_csv(str(DATA_CSV))


@router.post("/score-all/run")
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


@router.get("/leads/scored", response_model=List[LeadScored])
def get_scored_leads():
    if not OUTPUT_JSON.exists():
        raise HTTPException(
            status_code=404,
            detail="Aún no existe output/leads_scored.json. Ejecuta POST /pipeline/run primero."
        )

    with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data

#LangChain endpoints
@router.post("/score-ai", response_model=LeadScoredAIResponse)
def score_one_ai(lead: LeadIn):
    scored = score_lead(lead.model_dump())

    ai = enrich_lead_ai(
        lead=lead.model_dump(),
        rule_score=scored["score"],
        prioridad=scored["prioridad"],
        razones_reglas=scored["razones"],
    )

    return {
        "rule_score": scored["score"],
        "ai": ai
    }

@router.post("/enrich-all/run")
def score_all_ai():

    if not DATA_CSV.exists():
        raise HTTPException(status_code=404, detail=f"No existe el CSV: {DATA_CSV}")
    
    OUTPUT_DIR.mkdir(exist_ok=True)

    leads = read_leads_csv(str(DATA_CSV))
    enricheds = enrich_all_ai(leads)

    #pasamos el objeto pydantic a dict para evitar errores:
    payload = [e.model_dump() for e in enricheds]

#persistimos en la bd
    for e in payload:
        save_enriched_lead(e, status="ok")

    write_json(payload, str(OUTPUT_ENRICH_JSON))

    return {
        "status": "ok",
        "total": len(enricheds),
        "output_file": str(OUTPUT_ENRICH_JSON)
    }

@router.get("/leads/enriched", response_model=list[EnrichedLead])
def get_enriched_leads():
    if not OUTPUT_ENRICH_JSON.exists():
        raise HTTPException(404, "No existe output/leads_enriched.json. Ejecuta POST /enrich-all/run primero.")

    with open(OUTPUT_ENRICH_JSON, "r", encoding="utf-8") as f:
        return json.load(f)



#base datos

@router.get("/db/leads/enriched")
def get_enriched_leads_from_db():
    return get_leads_enriched()


@router.get("/db/leads/enriched/{lead_id}")
def get_enriched_lead_from_db(lead_id: int):
    lead = get_enriched_lead_by_id(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} no existe en la BD")
    return lead