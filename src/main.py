from fastapi import FastAPI
from src.router import router

app = FastAPI(
    title="Black Box Replacement",
    description="Reemplazo compatible del servicio heredado",
    version="0.1.0"
)

app.include_router(router)
