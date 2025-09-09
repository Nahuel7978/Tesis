# services/job_cleaner.py

import time
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from Services.docker_service import DockerService
from Services.core.config import Config
from Services.state_service import StateService
from Services.world_service import WorldService

logger = logging.getLogger("job_cleaner")

class JobCleanerService:
    """
    Servicio de limpieza de jobs que maneja el ciclo de vida completo:
    run -> ready -> finished -> expired -> deleted
    """
    
    def __init__(self):
        """
        Inicializa el limpiador de jobs
        
        Args:
            jobs_storage_path: Ruta donde se almacenan los jobs
        """
        self.__config = Config()
        self.__jobs_path = Path(self.__config.get_storage_path())
        self.__stateService = StateService()
        self.__dockerService = DockerService()
        self.__worldService = WorldService()
        self.__containersUp=self.__dockerService.list_running_simulations()
        
        # Configuración de TTL (Time To Live)
        self.__ttlConfig = self.__config.get_ttl_config()
        
        logger.info(f"JobCleaner inicializado. Jobs path: {self.__jobs_path}")
    
    def process_all_jobs(self):
        """
        Procesa todos los jobs según su estado actual.
        Este es el método principal que se ejecuta periódicamente.
        """
        start_time = time.time()
        processed_jobs = 0
        
        try:
            logger.debug("Iniciando proceso de limpieza de jobs...")
            
            if not self.__jobs_path.exists():
                logger.warning(f"Directorio de jobs no existe: {self.__jobs_path}")
                return
            
            # Obtener todos los directorios de jobs
            job_dirs = [d for d in self.__jobs_path.iterdir() if d.is_dir() and d.name.startswith('job_')]
            
            logger.debug(f"Encontrados {len(job_dirs)} directorios de jobs")
            
            self._get_running_containers()

            for job_dir in job_dirs:
                try:
                    self._process_single_job(job_dir)
                    processed_jobs += 1
                except Exception as e:
                    logger.error(f"❌ Error procesando job {job_dir.name}: {e}")
            
            elapsed = time.time() - start_time
            logger.debug(f"✅ Proceso completado: {processed_jobs} jobs procesados en {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error en process_all_jobs: {e}")
            
    def deep_cleanup(self):
        """Limpieza profunda: busca contenedores huérfanos, archivos temporales, etc."""
        logger.info("Ejecutando limpieza profunda...")
        try:
            
            for container in self.__containersUp:
                container_name = container.name
                job_id = container_name.replace("webots_job_", "")
                job_dir = self.__jobs_path / job_id
                
                if not job_dir.exists():
                    logger.warning(f"Contenedor huérfano encontrado: {container_name}")
                    self.__dockerService.stop_simulation(job_id)
            
        except Exception as e:
            logger.error(f"❌ Error en deep_cleanup: {e}")
    
    def log_stats(self):
        """Registra estadísticas de jobs para monitoreo"""
        try:
            if not self.__jobs_path.exists():
                print(f"{self.__jobs_path} no existe.")
                return
            
            job_dirs = [d for d in self.__jobs_path.iterdir() if d.is_dir() and d.name.startswith('job_')]
            stats = {"total": len(job_dirs), "WAIT":0,"RUNNING":0, "ERROR":0, "READY":0, "TERMINATED":0, "orphaned": 0}
            
            for job_dir in job_dirs:
                state_file = job_dir / "logs" / "state.json"
                
                if not state_file.exists():
                    stats["orphaned"] += 1
                    continue
                
                try:
                    self.__stateService.set_path(state_file)
                    state = self.__stateService.read_state() 
                    status = state.get("state", "unknown")
                    if status in stats:
                        stats[status] += 1
                    else:
                        stats["orphaned"] += 1
                except:
                    stats["orphaned"] += 1
            
            logger.info(f"📊 Job Stats: {stats}")
            
        except Exception as e:
            logger.error(f"❌ Error generando estadísticas: {e}")
    
    def _process_single_job(self, job_dir: Path):
        """Procesa un job individual según su estado"""
        job_id = job_dir.name
        state_file = job_dir / "logs" / "state.json"
        
        # Si no existe archivo de estado, es un job huérfano
        if not state_file.exists():
            self._handle_orphaned_job(job_dir,state_file)
            return
        
        try:
            # Leer estado actual
            self.__stateService.set_path(state_file)
            state = self.__stateService.read_state()
            
            # Procesar según estado
            if state["state"]== "RUNNING":
                self._handle_running_job(job_dir, state)
            elif state["state"] == "READY":
                self._handle_ready_job(job_dir, state)
            elif state["state"] == "ERROR":
                self._handle_error_job(job_dir, state)
            elif state["state"] == "TERMINATED":
                self._delete_job_completely(job_dir)
            else:
                logger.warning(f"⚠️ Estado desconocido '{state['status']}' en job {job_id}")
                
        except Exception as e:
            logger.error(f"❌ Error procesando estado del job {job_id}: {e}")
    
    def _handle_running_job(self, job_dir: Path, state:Dict):
        """Maneja jobs en estado 'run'"""
        job_id = job_dir.name
        try:
            container_name = f"webots_job_{job_id}"
    
            if(not(container_name in self.__containersUp)):
                self.__stateService.set_state(1)
                
            
            init_time = datetime.fromisoformat(state["init_timestamp"])
            diff = datetime.now()-init_time
            if(diff>=timedelta(hours=self.__ttlConfig["failed_jobs_hours"])):
                logger.warning(f"Job {job_id} excede el limite de tiempo de entrenamiento")
                self.__dockerService.stop_simulation(job_id)
                self.__stateService.set_state(2,"El job ha sido detenido por exceder el tiempo máximo de entrenamiento")
            
        except Exception as e:
            logger.error(f"Error verificando contenedor {job_id}: {e}")
    
    def _handle_ready_job(self, job_dir: Path, state: Dict):
        """Maneja jobs en estado 'ready' - limpia contenedor y marca como finished"""
        job_id = job_dir.name
        
        logger.info(f"Limpiando job {job_id} (ready -> finished)")
        
        self.__worldService.delete_world(job_dir)

        if(self._should_expire_job(job_dir, state)):
            self.__stateService.set_state(4)
            logger.info(f"✅ Job {job_id} marcado como terminated")
           
    def _handle_error_job(self, job_dir: Path, state: Dict):
        """Maneja jobs en estado 'error' - limpia contenedor y marca como finished"""
        job_id = job_dir.name
        container_name = f"webots_job_{job_id}"
        if(container_name in self.__containersUp):
            self.__dockerService.stop_simulation(job_id)
        
        self.__worldService.delete_world(job_dir)

        if(self._should_expire_job(job_dir, state)):
            logger.info(f"Job {job_id} se eliminará del storage en una hora")
            self.__stateService.set_state(4)
            logger.info(f"✅ Job {job_id} marcado como terminated")

    def _handle_orphaned_job(self, job_dir: Path, state_file: Path):
        """Maneja jobs sin archivo de estado (huérfanos)"""
        job_id = job_dir.name
        
        # Verificar si hay contenedores corriendo para este job
        container_name = f"webots_job_{job_id}"
        
        try:
            if(container_name in self.__containersUp):
                self.__dockerService.stop_simulation(job_id)
        
        except Exception as e:
            logger.error(f"Error limpiando contenedores huérfanos: {e}")
        
        self.__stateService.set_path(state_file)
        self.__stateService.create_state()
        self.__stateService.set_state(2,"Contenedor sin estado asociado, marcado como ERROR")
        logger.info(f"Job huérfano {job_id} marcado como ERROR")
    
    def _should_expire_job(self, job_dir: Path, state: Dict) -> bool:
        """Determina si un job debe expirar basado en TTL y success/failure"""
        
        # Buscar archivo del modelo entrenado
        model_file = job_dir / "trained_model" / "model.zip"
        
        if model_file.exists():
            # Usar timestamp del modelo como referencia
            model_time = datetime.fromtimestamp(model_file.stat().st_mtime)
            reference_time = model_time
            ttl_hours = self.__ttlConfig["completed_jobs_hours"]
        else:
            # Si no hay modelo, probablemente falló
            finished_at = state.get("end_timestamp")
            if finished_at:
                reference_time = datetime.fromisoformat(finished_at)
            else:
                reference_time = datetime.now()  # Fallback
            
            ttl_hours = self.__ttlConfig["failed_jobs_hours"]
        
        # Calcular si ha expirado
        ttl_delta = timedelta(hours=ttl_hours)
        return datetime.now() - reference_time > ttl_delta
    
    def _delete_job_completely(self, job_dir: Path):
        """Elimina un job completamente del sistema de archivos"""
        import shutil
        
        try:
            shutil.rmtree(job_dir)
            logger.info(f"Job {job_dir.name} eliminado completamente")
        except Exception as e:
            logger.error(f"❌ Error eliminando job {job_dir.name}: {e}")

    def _get_running_containers(self):
        """Obtiene la lista actualizada de contenedores corriendo"""
        self.__containersUp = self.__dockerService.list_running_simulations()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    job_cleaner = JobCleanerService()
    job_cleaner.log_stats()
    #job_cleaner.process_all_jobs()
    #job_cleaner.deep_cleanup()
    job_cleaner.log_stats()
    
    
    