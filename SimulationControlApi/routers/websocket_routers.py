import json
import logging
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from Services.ws_conection_service import ConnectionManagerService

# Configurar logging
logger = logging.getLogger(__name__)

router = APIRouter()


# Instancia global del connection manager
connection_manager = ConnectionManagerService()

@router.websocket("/jobs/{job_id}/metrics/stream")
async def stream_training_metrics(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint para streaming de métricas de entrenamiento en tiempo real
    
    Args:
        websocket: Conexión WebSocket
        job_id: ID del job del cual obtener las métricas
    
    Returns:
        Stream continuo de métricas en formato JSON
    """
    
    # Verificar que el job existe
    job_path = Path(f"Storage/Jobs/{job_id}")
    if not job_path.exists():
        await websocket.close(code=4004, reason="Job not found")
        return
    
    await connection_manager.connect(websocket, job_id)
    
    try:
        while True:
            # Mantener la conexión viva
            # El streaming real se maneja a través del file watcher
            await websocket.receive_text()  # Esperar por ping del cliente
            
    except WebSocketDisconnect:
        logger.info(f"Cliente desconectado del stream de job {job_id}")
    except Exception as e:
        logger.error(f"Error en WebSocket para {job_id}: {e}")
    finally:
        await connection_manager.disconnect(websocket, job_id)