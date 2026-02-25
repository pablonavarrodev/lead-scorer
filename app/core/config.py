#Rutas a los ficheros
from pathlib import Path

#Saco la ruta de este archivo, la paso a absoluta, y subo 2 escalones a la ruta padre. file es main.py
BASE_DIR = Path(__file__).resolve().parents[2] 
DATA_CSV = BASE_DIR / "data" / "leads.csv"
OUTPUT_JSON = BASE_DIR / "output" / "leads_scored.json"
OUTPUT_DIR = BASE_DIR / "output"
