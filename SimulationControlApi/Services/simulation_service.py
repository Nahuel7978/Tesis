import os
import re
import shutil
from pathlib import Path
import logging
from Services.world_service import WorldService
from Services.docker_service import DockerService

logger = logging.getLogger(__name__)

class SimulationService:
    def __init__(self):
        self.storage_path = Path("Storage/Jobs")
        self._current_max_id = None
        self._initialize_max_id()
        self.world_service = WorldService()
        self.docker_service = DockerService()
        
        
    def _initialize_max_id(self) -> None:
            """
            Inicializa el ID máximo analizando las carpetas existentes en Storage/Jobs.
            Se ejecuta al levantar el servicio.
            """
            try:
                self._current_max_id = self._get_max_job_id()
                logger.info(f"ID máximo inicializado: {self._current_max_id}")
            except Exception as e:
                logger.error(f"Error al inicializar el ID máximo: {e}")
                self._current_max_id = 0
        
    def _get_max_job_id(self) -> int:
            """
            Analiza las carpetas en Storage/Jobs y retorna el ID más grande encontrado.
            Si no hay carpetas, retorna 0.
            
            Returns:
                int: El ID más grande encontrado, o 0 si no hay carpetas
            """
            # Crear el directorio si no existe
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
            max_id = 0
            job_pattern = re.compile(r'^job_(\d+)$')
            
            try:
                # Listar todas las carpetas en Storage/Jobs
                for item in self.storage_path.iterdir():
                    if item.is_dir():
                        match = job_pattern.match(item.name)
                        if match:
                            job_id = int(match.group(1))
                            max_id = max(max_id, job_id)
                            logger.debug(f"Carpeta encontrada: {item.name}, ID: {job_id}")
                
                logger.info(f"ID máximo encontrado en carpetas existentes: {max_id}")
                return max_id
                
            except Exception as e:
                logger.error(f"Error al analizar carpetas de jobs: {e}")
                return 0
            
    def _get_next_job_id(self) -> int:
        """
        Obtiene el siguiente ID único para un nuevo job.
        
        Returns:
            int: El siguiente ID disponible
        """
        if self._current_max_id is None:
            self._initialize_max_id()
        
        self._current_max_id += 1
        logger.info(f"Generando nuevo job ID: {self._current_max_id}")
        return self._current_max_id
    
    def set_job_directory(self):
         id = self._get_next_job_id()
         job = "job_"+str(id)
         return self.world_service.setup_job_workspace(job),job

    def start_job(self, job:str, zip_path:Path):
        try:
            extracted_path = self.world_service.extract_world_archive(zip_path, job)

            name,controller,env_class = self.world_service.get_robot(job)
            
            wbt = self.world_service.validate_world(name,Path(extracted_path))

            
            self.world_service.patch_world_controllers(name,wbt)

            
            logger.info(f"Iniciando contenedor para el job {job} con el mundo {wbt.name}")
            base_dir = Path(__file__).parent.parent 
            wbt_path=(base_dir / wbt).resolve()
            return self.docker_service.start_simulation_for_job(job, wbt_path)
            
        except Exception as e:
            logger.error(f"Falló el inicio del job {job}: {e}")
            # ... Eliminar directorio ....
            raise
        
    def cancel_job(self, job_id: str):
        """
        Cancela un job en ejecución.
        
        Args:
            job_id (str): El ID del job a cancelar.
        """
        try:
            logger.info(f"Cancelando el job {job_id}")
            self.docker_service.stop_simulation(job_id)        
            shutil.rmtree(self.storage_path / job_id)
            logger.info(f"Job {job_id} cancelado exitosamente")
        except Exception as e:
            logger.error(f"Error al cancelar el job {job_id}: {e}")
            raise