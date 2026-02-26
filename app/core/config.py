#Rutas a los ficheros
import os
from pathlib import Path
from dotenv import load_dotenv

#carga las variables del .env en el sistema para poder usarlas
load_dotenv()

#Saco la ruta de este archivo, la paso a absoluta, y subo 3 escalones a la ruta padre.
BASE_DIR = Path(__file__).resolve().parents[2] 

#con getenv mandamos dos argumentos ya que por ejemplo el ci de github no tiene acceso al .env entonces asi sabe que ruta usar si no existe .env
DATA_CSV = BASE_DIR / os.getenv("DATA_CSV_PATH", "data/leads.csv") 

OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
OUTPUT_JSON = OUTPUT_DIR / os.getenv("OUTPUT_FILE", "leads_scored.json")
