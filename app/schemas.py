from pydantic import BaseModel, EmailStr, Field
from typing import List


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