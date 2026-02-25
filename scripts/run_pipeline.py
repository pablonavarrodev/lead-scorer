import os

from app.services.storage import read_leads_csv, write_json
from app.services.scoring import score_all

#Me aseguro que exista la carpeta output
os.makedirs("output", exist_ok=True)

leads = read_leads_csv("data/leads.csv")

score_leads = score_all(leads)

write_json(score_leads, "output/leads_scored.json")