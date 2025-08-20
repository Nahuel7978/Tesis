# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers.routers_api import router as api_router
#from Services.core.config import CORS_ORIGINS  # tu configuración central
import logging

logger = logging.getLogger("scapi")

# Eventos (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código de inicialización
    logger.info("API arrancando: inicializando recursos...")
    yield
    # Código de limpieza
    logger.info("API apagándose: cerrando recursos...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Simulation Control API",
        version="0.1.0",
        description="API para lanzar entrenamientos Webots + DeepBots + Stable Baseline3",
        lifespan=lifespan
    )

    # Middlewares: CORS ejemplo (ajustar CORS_ORIGINS en config)
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    """
    # Routers
    app.include_router(api_router, prefix="/SimulationControlApi/v1")

    return app

app = create_app()
