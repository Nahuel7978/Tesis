import asyncio
import json
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import aiofiles
from Services.state_service import StateService

# Configurar logging
logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManagerService:
    """Maneja las conexiones WebSocket activas por job_id"""
    
    def __init__(self):
        # job_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # job_id -> Observer (file watcher)
        self.file_observers: Dict[str, Observer] = {}  # type: ignore 
        # job_id -> Observer (state watcher)
        self.state_observers: Dict[str, Observer] = {} # type: ignore 
        # job_id -> último contenido leído
        self.last_metrics: Dict[str, dict] = {}
        # job_id -> StateService instance
        self.state_services: Dict[str, StateService] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """Conecta un WebSocket y configura el file watcher si es necesario"""
        
        # Verificar estado del job antes de aceptar conexión
        state_service = self._get_state_service(job_id)
        try:
            current_state = state_service.get_state()
        except Exception as e:
            logger.error(f"Error obteniendo estado del job {job_id}: {e}")
            await websocket.close(code=4003, reason="Error reading job state")
            return
        
        # Solo permitir conexiones si el estado es WAIT o RUNNING
        if current_state not in ["WAIT", "RUNNING"]:
            await websocket.close(
                code=4001, 
                reason=f"Training finished. Current state: {current_state}"
            )
            return
        
        await websocket.accept()
        
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        
        self.active_connections[job_id].add(websocket)
        
        # Si es la primera conexión para este job, iniciar watchers
        if len(self.active_connections[job_id]) == 1:
            await self._start_file_watcher(job_id)
            await self._start_state_watcher(job_id)
        
        # Enviar último metric conocido si existe
        if job_id in self.last_metrics:
            try:
                await websocket.send_text(json.dumps(self.last_metrics[job_id]))
            except Exception as e:
                logger.error(f"Error enviando último metric a nueva conexión: {e}")
        
        # Enviar estado actual
        try:
            await websocket.send_text(json.dumps({
                "type": "status",
                "state": current_state,
                "message": f"Connected to job {job_id}. Current state: {current_state}"
            }))
        except Exception as e:
            logger.error(f"Error enviando estado inicial: {e}")
    
    async def disconnect(self, websocket: WebSocket, job_id: str):
        """Desconecta un WebSocket y limpia resources si es necesario"""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            
            # Si no quedan conexiones, detener watchers
            if len(self.active_connections[job_id]) == 0:
                await self._stop_file_watcher(job_id)
                await self._stop_state_watcher(job_id)
                del self.active_connections[job_id]
                # Limpiar state service del cache
                if job_id in self.state_services:
                    del self.state_services[job_id]
    
    async def broadcast_to_job(self, job_id: str, message: dict):
        """Envía un mensaje a todas las conexiones de un job específico"""
        if job_id not in self.active_connections:
            return
        
        # Actualizar último metric si es una métrica
        if message.get("type") != "status":
            self.last_metrics[job_id] = message
        
        disconnected = []
        for websocket in self.active_connections[job_id].copy():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error enviando mensaje a WebSocket: {e}")
                disconnected.append(websocket)
        
        # Limpiar conexiones desconectadas
        for ws in disconnected:
            await self.disconnect(ws, job_id)
    
    async def close_job_connections(self, job_id: str, reason: str = "Training finished"):
        """Cierra todas las conexiones de un job específico"""
        if job_id not in self.active_connections:
            return
        
        # Enviar mensaje de finalización antes de cerrar
        final_message = {
            "type": "status",
            "state": "FINISHED",
            "message": reason,
            "final": True
        }
        
        for websocket in self.active_connections[job_id].copy():
            try:
                await websocket.send_text(json.dumps(final_message))
                await websocket.close(code=1000, reason=reason)
            except Exception as e:
                logger.error(f"Error cerrando conexión WebSocket: {e}")
        
        # Limpiar recursos
        await self._stop_file_watcher(job_id)
        await self._stop_state_watcher(job_id)
        if job_id in self.active_connections:
            del self.active_connections[job_id]
        if job_id in self.state_services:
            del self.state_services[job_id]
    
    def _get_state_service(self, job_id: str) -> StateService:
        """Obtiene o crea una instancia de StateService para el job"""
        if job_id not in self.state_services:
            state_path = Path(f"Storage/Jobs/{job_id}/logs/state.json")
            state_service = StateService()
            state_service.set_path(state_path)
            self.state_services[job_id] = state_service
        
        return self.state_services[job_id]
    
    async def _start_state_watcher(self, job_id: str):
        """Inicia el state watcher para un job específico"""
        state_file = Path(f"Storage/Jobs/{job_id}/logs/state.json")
        
        if not state_file.parent.exists():
            logger.warning(f"Directorio de logs no existe para job {job_id}")
            return
        
        # Configurar state watcher
        loop = asyncio.get_running_loop()
        event_handler = StateFileHandler(job_id, self, loop)
        observer = Observer()
        observer.schedule(
            event_handler, 
            str(state_file.parent), 
            recursive=False
        )
        observer.start()
        
        self.state_observers[job_id] = observer
        logger.info(f"State watcher iniciado para job {job_id}")
    
    async def _stop_state_watcher(self, job_id: str):
        """Detiene el state watcher para un job específico"""
        if job_id in self.state_observers:
            observer = self.state_observers[job_id]
            observer.stop()
            observer.join()
            del self.state_observers[job_id]
            logger.info(f"State watcher detenido para job {job_id}")
    
    async def _start_file_watcher(self, job_id: str):
        """Inicia el file watcher para un job específico"""
        metrics_file = Path(f"Storage/Jobs/{job_id}/logs/training_metrics.jsonl")
        
        if not metrics_file.parent.exists():
            logger.warning(f"Directorio de logs no existe para job {job_id}")
            return
        
        # Leer último metric si el archivo ya existe
        if metrics_file.exists():
            await self._read_last_metric(job_id, str(metrics_file))
        
        # Configurar file watcher
        loop = asyncio.get_running_loop()
        event_handler = MetricsFileHandler(job_id, self, loop)
        observer = Observer()
        observer.schedule(
            event_handler, 
            str(metrics_file.parent), 
            recursive=False
        )
        observer.start()
        
        self.file_observers[job_id] = observer
        logger.info(f"File watcher iniciado para job {job_id}")
    
    async def _stop_file_watcher(self, job_id: str):
        """Detiene el file watcher para un job específico"""
        if job_id in self.file_observers:
            observer = self.file_observers[job_id]
            observer.stop()
            observer.join()
            del self.file_observers[job_id]
            logger.info(f"File watcher detenido para job {job_id}")
    
    async def _read_last_metric(self, job_id: str, file_path: str):
        """Lee la última línea del archivo de metrics"""
        try:
            async with aiofiles.open(file_path, 'r') as f:
                lines = await f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if last_line:
                        metric = json.loads(last_line)
                        self.last_metrics[job_id] = metric
        except Exception as e:
            logger.error(f"Error leyendo último metric para job {job_id}: {e}")

class StateFileHandler(FileSystemEventHandler):
    """Handler para eventos de cambio en el archivo de estado"""
    
    def __init__(self, job_id: str, connection_manager: ConnectionManagerService, loop):
        self.job_id = job_id
        self.connection_manager = connection_manager
        self.state_filename = "state.json"
        self.loop = loop
    
    def on_modified(self, event):
        """Se ejecuta cuando el archivo de estado es modificado"""
        if event.is_directory:
            return
        
        if event.src_path.endswith(self.state_filename):
            asyncio.run_coroutine_threadsafe(
                    self._process_state_change(event.src_path),
                    self.loop
                    )
    
    async def _process_state_change(self, file_path: str):
        """Procesa el cambio en el archivo de estado"""
        try:
            # Pequeña espera para asegurar que el archivo se escribió completamente
            await asyncio.sleep(0.1)
            
            state_service = self.connection_manager._get_state_service(self.job_id)
            current_state = state_service.get_state()
            
            # Crear mensaje de estado
            status_message = {
                "type": "status",
                "state": current_state,
                "message": f"Job state changed to {current_state}",
                "timestamp": datetime.now().isoformat()
            }
            
            # Si el estado cambió a algo que no sea WAIT o RUNNING, cerrar conexiones
            if current_state not in ["WAIT", "RUNNING"]:
                logger.info(f"Job {self.job_id} state changed to {current_state}, closing connections")
                await self.connection_manager.close_job_connections(
                    self.job_id, 
                    f"Training finished. Final state: {current_state}"
                )
            else:
                # Solo enviar actualización de estado
                await self.connection_manager.broadcast_to_job(
                    self.job_id, 
                    status_message
                )
                
        except Exception as e:
            logger.error(f"Error procesando cambio de estado: {e}")


class MetricsFileHandler(FileSystemEventHandler):
    """Handler para eventos de cambio en el archivo de metrics"""
    
    def __init__(self, job_id: str, connection_manager: ConnectionManagerService, loop):
        self.job_id = job_id
        self.connection_manager = connection_manager
        self.metrics_filename = "training_metrics.jsonl"
        self.loop = loop
    
    def on_modified(self, event):
        """Se ejecuta cuando el archivo es modificado"""
        if event.is_directory:
            return
        
        if event.src_path.endswith(self.metrics_filename):
            asyncio.run_coroutine_threadsafe(
                    self._process_file_change(event.src_path),
                    self.loop
                    )
    
    async def _process_file_change(self, file_path: str):
        """Procesa el cambio en el archivo y envía el último metric"""
        try:
            # Verificar que el job aún esté en estado válido para métricas
            state_service = self.connection_manager._get_state_service(self.job_id)
            current_state = state_service.get_state()
            
            if current_state not in ["WAIT", "RUNNING"]:
                logger.info(f"Job {self.job_id} no longer in active state ({current_state}), skipping metrics update")
                return
            
            # Pequeña espera para asegurar que el archivo se escribió completamente
            await asyncio.sleep(0.1)
            
            async with aiofiles.open(file_path, 'r') as f:
                lines = await f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if last_line:
                        metric = json.loads(last_line)
                        # Agregar información de tipo para distinguir de mensajes de estado
                        metric["type"] = "metric"
                        await self.connection_manager.broadcast_to_job(
                            self.job_id, 
                            metric
                        )
        except Exception as e:
            logger.error(f"Error procesando cambio de archivo: {e}")
