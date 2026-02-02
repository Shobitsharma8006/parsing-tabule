from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Tableau Parsing Service")
app.include_router(router)

