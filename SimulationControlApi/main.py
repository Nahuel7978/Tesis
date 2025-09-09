# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from routers.routers_api import router as api_router
from routers.websocket_routers import router as websocket_router
from SimulationControlApi.Services.job_cleaner_service import JobCleanerService
import logging
import atexit

logger = logging.getLogger("scapi")
scheduler = None
job_cleaner = None


# Eventos (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código de inicialización
    logger.info("API arrancando: inicializando recursos...")
    try:
        # Configurar y arrancar scheduler
        setup_scheduler()
        
        # Ejecutar una limpieza inicial
        if job_cleaner:
            logger.info("🧹 Ejecutando limpieza inicial...")
            job_cleaner.process_all_jobs()
            
        logger.info("✅ Inicialización completada")
        
    except Exception as e:
        logger.error(f"❌ Error durante inicialización: {e}")
        raise
    
    yield
    # Código de limpieza
    logger.info("API apagándose: cerrando recursos...")
    shutdown_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Simulation Control API",
        version="0.1.0",
        description="API para lanzar entrenamientos Webots + DeepBots + Stable Baseline3",
        lifespan=lifespan
    )

    # Middlewares: CORS ejemplo (ajustar CORS_ORIGINS en config)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Routers
    app.include_router(api_router, prefix="/SimulationControlApi/v1")
    app.include_router(websocket_router, prefix="/SimulationControlApi/ws/v1")

    return app

def setup_scheduler():
    """Configura y arranca el scheduler con los jobs de limpieza"""
    global scheduler, job_cleaner
    
    try:
        # Crear scheduler
        scheduler = BackgroundScheduler(
            timezone="UTC",
            job_defaults={
                'coalesce': False,  # No agrupar jobs perdidos
                'max_instances': 1,  # Solo una instancia del job corriendo a la vez
                'misfire_grace_time': 30  # 30 segundos de gracia para jobs atrasados
            }
        )
        
        # Crear instancia del limpiador
        job_cleaner = JobCleanerService()
        
        # Configurar jobs programados
        scheduler.add_job(
            func=job_cleaner.process_all_jobs,
            trigger=IntervalTrigger(minutes=30),
            id='job_cleaner_main',
            name='Job Cleaner - Main Process',
            replace_existing=True
        )
        
        # Job adicional para limpieza profunda (menos frecuente)
        scheduler.add_job(
            func=job_cleaner.deep_cleanup,
            trigger=IntervalTrigger(hours=1), 
            id='job_cleaner_deep',
            name='Job Cleaner - Deep Cleanup',
            replace_existing=True
        )
        
        # Job para estadísticas/monitoreo (opcional)
        scheduler.add_job(
            func=job_cleaner.log_stats,
            trigger=IntervalTrigger(minutes=90), 
            id='job_stats',
            name='Job Statistics Logger',
            replace_existing=True
        )
        
        # Arrancar scheduler
        scheduler.start()
        logger.info("Scheduler de jobs iniciado exitosamente")
        
        # Registrar función de limpieza para cuando se cierre el proceso
        atexit.register(shutdown_scheduler)
        
    except Exception as e:
        logger.error(f"❌ Error al configurar scheduler: {e}")
        raise

def shutdown_scheduler():
    """Cierra el scheduler de manera ordenada"""
    global scheduler
    
    if scheduler and scheduler.running:
        try:
            logger.info("🛑 Cerrando scheduler de jobs...")
            scheduler.shutdown(wait=True)
            logger.info("✅ Scheduler cerrado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error al cerrar scheduler: {e}")

app = create_app()
