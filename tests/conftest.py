import sys
from pathlib import Path

#esto es porque pytest no encuentra el paquete app en el sys.path y asi se lo añadimos
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))