import asyncio
import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from app.repositories.lead_repository import exist_enriched_lead
from app.schemas import LeadAIResult, EnrichedLead
from app.services.scoring import score_lead

load_dotenv()


def _get_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=250,
    )


_PROMPT = """Eres un asistente comercial.

TAREA:
Analiza el lead y devuelve SOLO un JSON válido (sin texto extra).

REGLAS:
- Basate únicamente en los datos proporcionados.
- No inventes información externa.
- Campos obligatorios:
    - ai_summary: resumen en 1-2 líneas (español)
    - risk_flags: lista de strings (puede ser [])
    - next_action: uno de ["call","email","validate_data","discard"]
    - reasoning_short: 1-2 frases justificando next_action (español)

PISTAS PARA DECIDIR:
- Si hay incoherencias claras (ej: ingresos muy altos con 1-2 empleados) -> next_action="validate_data" y añade risk_flags.
- Si lead muy frío (muchos días desde último contacto) -> suele ser "email" o "discard" según score/interés.
- Si score alto y contacto reciente/interés alto -> suele ser "call".
- risk_flags sugeridos (usa los que apliquen):
    - "data_inconsistency"
    - "cold_lead"
    - "low_interest"
    - "saturated_sector"
    - "missing_or_suspicious_email"

DATOS:
lead={lead_json}
rule_score={rule_score}
prioridad={prioridad}
razones_reglas={razones_json}
"""


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No se encontró un objeto JSON en la respuesta del LLM")

    return json.loads(text[start:end + 1])


def enrich_lead_ai(
    lead: Dict[str, Any],
    rule_score: int,
    prioridad: str,
    razones_reglas: List[str],
) -> LeadAIResult:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY no está configurada")

    prompt = _PROMPT.format(
        lead_json=json.dumps(lead, ensure_ascii=False),
        rule_score=rule_score,
        prioridad=prioridad,
        razones_json=json.dumps(razones_reglas, ensure_ascii=False),
    )

    llm = _get_llm()
    resp = llm.invoke(prompt)
    raw = resp.content

    try:
        data = _extract_json(raw)
        return LeadAIResult(**data)
    except Exception:
        fix_prompt = (
            "Tu respuesta anterior no era un JSON válido o no cumplía el schema.\n"
            "Devuelve SOLO el JSON válido con los campos exactos.\n\n"
            f"RESPUESTA ANTERIOR:\n{raw}"
        )
        resp2 = llm.invoke(fix_prompt)
        data2 = _extract_json(resp2.content)
        return LeadAIResult(**data2)


async def enrich_lead_ai_async(
    lead: Dict[str, Any],
    rule_score: int,
    prioridad: str,
    razones_reglas: List[str],
) -> LeadAIResult:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY no está configurada")

    prompt = _PROMPT.format(
        lead_json=json.dumps(lead, ensure_ascii=False),
        rule_score=rule_score,
        prioridad=prioridad,
        razones_json=json.dumps(razones_reglas, ensure_ascii=False),
    )

    llm = _get_llm()
    resp = await llm.ainvoke(prompt)
    raw = resp.content

    try:
        data = _extract_json(raw)
        return LeadAIResult(**data)
    except Exception:
        fix_prompt = (
            "Tu respuesta anterior no era un JSON válido o no cumplía el schema.\n"
            "Devuelve SOLO el JSON válido con los campos exactos.\n\n"
            f"RESPUESTA ANTERIOR:\n{raw}"
        )
        resp2 = await llm.ainvoke(fix_prompt)
        data2 = _extract_json(resp2.content)
        return LeadAIResult(**data2)


async def _enrich_one_lead(
    lead: Dict[str, Any],
    mode: str,
    semaphore: asyncio.Semaphore,
) -> EnrichedLead | None:
    lead_id = int(lead["id"])

    if mode == "skip" and exist_enriched_lead(lead_id):
        return None

    lead_score = score_lead(lead)

    async with semaphore:
        lead_enrich = await enrich_lead_ai_async(
            lead,
            lead_score["score"],
            lead_score["prioridad"],
            lead_score["razones"],
        )

    return EnrichedLead(
        lead=lead,
        rule_score=lead_score["score"],
        prioridad=lead_score["prioridad"],
        razones=lead_score["razones"],
        ai=lead_enrich,
    )


async def enrich_all_ai(leads, mode, max_concurrency: int = 5) -> tuple[List[EnrichedLead], int]:
    semaphore = asyncio.Semaphore(max_concurrency)

    tasks = [
        _enrich_one_lead(lead, mode=mode, semaphore=semaphore)
        for lead in leads
    ]

    results = await asyncio.gather(*tasks)

    enriched = [r for r in results if r is not None]
    skipped = len(results) - len(enriched)

    return enriched, skipped