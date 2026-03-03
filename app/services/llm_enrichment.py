import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from app.schemas import LeadAIResult

load_dotenv()

# Instancia global (simple y suficiente para empezar)
_llm = ChatOpenAI(
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
    
    #pasa a JSON aunque el modelo meta texto extra. 
    text = text.strip()
    # caso ideal
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass #esto no hace nada y sigue

    # busca { y } 
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start: #-1 no encontrado, y mira el orden de las llaves tmbn
        raise ValueError("No se encontró un objeto JSON en la respuesta del LLM")
    
    #caso texto limpiado
    return json.loads(text[start : end + 1]) #el +1 es para incluir el end


def enrich_lead_ai(   #esto son parametros normales pero indicamos el tipo
    lead: Dict[str, Any],
    rule_score: int,
    prioridad: str,
    razones_reglas: List[str],
) -> LeadAIResult:  #aqui indicamos que devuelve un objeto de ese tipo
    
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY no está configurada")

    prompt = _PROMPT.format(
        #pasamos los dict a json para que el llm no se raye, lo del ascii para que no se  raye con acentos
        lead_json=json.dumps(lead, ensure_ascii=False), 
        rule_score=rule_score,
        prioridad=prioridad,
        razones_json=json.dumps(razones_reglas, ensure_ascii=False),
    )

    #esto devuelve un objeto!
    resp = _llm.invoke(prompt)
    #solo texto generado
    raw = resp.content

    try:
        data = _extract_json(raw)
        return LeadAIResult(**data)
    except Exception:
        #si da error JSON invalido, reintentamos.
        fix_prompt = (
            "Tu respuesta anterior no era un JSON válido o no cumplía el schema.\n"
            "Devuelve SOLO el JSON válido con los campos exactos.\n\n"
            f"RESPUESTA ANTERIOR:\n{raw}" #le mandamos raw para que tenga la respuesta
        )
        resp2 = _llm.invoke(fix_prompt)
        data2 = _extract_json(resp2.content)
        return LeadAIResult(**data2)