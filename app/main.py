from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Lead Scorer API")

app.include_router(router)

