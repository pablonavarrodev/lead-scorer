from pydantic import BaseModel, EmailStr, Field
from typing import List, Literal


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

class LeadAIResult(BaseModel):
    ai_summary: str = Field(..., max_length=240)
    risk_flags: List[str]
    next_action: Literal["call", "email", "validate_data", "discard"]
    reasoning_short: str = Field(..., max_length=300)


class LeadScoredAIResponse(BaseModel):
    rule_score: int
    ai: LeadAIResult

class EnrichedLead(BaseModel):
    lead: LeadIn
    rule_score: int
    prioridad: str
    razones: List
    ai: LeadAIResult