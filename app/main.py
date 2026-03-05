from fastapi import FastAPI
from app.api.routes import router
from app.repositories.lead_repository import init_db

app = FastAPI(title="Lead Scorer API")

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(router)

