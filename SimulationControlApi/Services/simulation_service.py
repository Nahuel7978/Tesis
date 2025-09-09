import os
import re
import shutil
from pathlib import Path
import logging
import json
from Services.world_service import WorldService
from Services.state_service import StateService
from Services.docker_service import DockerService
from Services.core.config import Config

logger = logging.getLogger(__name__)

class SimulationService:
    def __init__(self):
        self.__storage_path = Path("Storage/Jobs")
        self.__current_max_id = None
        self._initialize_max_id()
        self.__config = Config()
        self.__jobs_storage_path = Path(self.__config.get_storage_path())
        self.__world_service = WorldService()
        self.__state_service = StateService()
        self.__docker_service = DockerService()
        
        
    def _initialize_max_id(self) -> None:
            """
            Inicializa el ID máximo analizando las carpetas existentes en Storage/Jobs.
            Se ejecuta al levantar el servicio.
            """
            try:
                self.__current_max_id = self._get_max_job_id()
                logger.info(f"ID máximo inicializado: {self.__current_max_id}")
            except Exception as e:
                logger.error(f"Error al inicializar el ID máximo: {e}")
                self.__current_max_id = 0
        
    def _get_max_job_id(self) -> int:
            """
            Analiza las carpetas en Storage/Jobs y retorna el ID más grande encontrado.
            Si no hay carpetas, retorna 0.
            
            Returns:
                int: El ID más grande encontrado, o 0 si no hay carpetas
            """
            # Crear el directorio si no existe
            self.__storage_path.mkdir(parents=True, exist_ok=True)
            
            max_id = 0
            job_pattern = re.compile(r'^job_(\d+)$')
            
            try:
                # Listar todas las carpetas en Storage/Jobs
                for item in self.__storage_path.iterdir():
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
        if self.__current_max_id is None:
            self._initialize_max_id()
        
        self.__current_max_id += 1
        logger.info(f"Generando nuevo job ID: {self.__current_max_id}")
        return self.__current_max_id
    
    def set_job_directory(self):
         id = self._get_next_job_id()
         job = "job_"+str(id)
         return self.__world_service.setup_job_workspace(job),job

    def start_job(self, job:str, zip_path:Path):
        try:
            extracted_path = self.__world_service.extract_world_archive(zip_path, job)

            name,controller,env_class = self.__world_service.get_robot(job)
            
            wbt = self.__world_service.validate_world(name,Path(extracted_path))

            
            self.__world_service.patch_world_controllers(name,wbt)

            self.__state_service.set_path(os.path.join(self.__jobs_storage_path,job,'logs','state.json'))
            self.__state_service.create_state()

            logger.info(f"Iniciando contenedor para el job {job} con el mundo {wbt.name}")
            base_dir = Path(__file__).parent.parent 
            wbt_path=(base_dir / wbt).resolve()
            return self.__docker_service.start_simulation_for_job(job, wbt_path)
            
        except Exception as e:
            logger.error(f"Falló el inicio del job {job}: {e}")
            shutil.rmtree(self.__storage_path / job)
            raise
        
    def cancel_job(self, job_id: str):
        """
        Cancela un job en ejecución.
        
        Args:
            job_id (str): El ID del job a cancelar.
        """
        try:
            logger.info(f"Cancelando el job {job_id}")
            self.__docker_service.stop_simulation(job_id)        
            shutil.rmtree(self.__storage_path / job_id)
            logger.info(f"Job {job_id} cancelado exitosamente")
        except Exception as e:
            logger.error(f"Error al cancelar el job {job_id}: {e}")
            raise

    def get_complete_state(self, job_id: str):
        """
        Obtiene el estado actual del job.
        
        Args:
            job_id (str): El ID del job.
        
        Returns:
            str: El estado actual del job.
        """
        try:
            logger.info(f"Obteniendo estado del job {job_id}")
            self.__state_service.set_path(os.path.join(self.__jobs_storage_path,job_id,'logs','state.json'))
            state = self.__state_service.read_state()
            return state
        except Exception as e:
            logger.error(f"Error al obtener el estado del job {job_id}: {e}")
            raise

    def get_logs(self, job_id: str):
        """
        Obtiene los logs del job.
        
        Args:
            job_id (str): El ID del job.
        
        Returns:
            str: Los logs del job.
        """
        try:
            logger.info(f"Obteniendo logs del job {job_id}")
            log_path = os.path.join(self.__jobs_storage_path, job_id, 'logs', 'training_metrics.jsonl')
            if os.path.exists(log_path):
                logs_list = []
                with open(log_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        logs_list.append(json.loads(line))
                return logs_list
            else:
                logger.warning(f"No se encontraron logs para el job {job_id}")
                return {"message": "No logs found."}
        except Exception as e:
            logger.error(f"Error al obtener los logs del job {job_id}: {e}")
            raise

    def get_tensorboard_path(self, job_id:str):
        """
        Obtiene la ruta del directorio de TensorBoard para el job.
        
        Args:
            job_id (str): El ID del job.
        
        Returns:
            str: La ruta del directorio de TensorBoard.
        """
        try:
            logger.info(f"Obteniendo ruta de TensorBoard para el job {job_id}")
            log_path = os.path.join(self.__jobs_storage_path, job_id, 'logs')
            if not os.path.isdir(log_path):
                raise FileNotFoundError(f"Directorio de logs no encontrado para el job {job_id}")
            
            self.__state_service.set_path(os.path.join(self.__jobs_storage_path,job_id,'logs','state.json'))
            if(self.__state_service.get_state() in ["WAIT","RUNNING"]):
                raise Exception(f"El job {job_id} aún está en ejecución. TensorBoard estará disponible una vez que el job haya finalizado.")

            tensorboard_file = None
            for filename in os.listdir(log_path):
                if filename.startswith("events.out.tfevents"):
                    tensorboard_file = filename
                    break

            if not tensorboard_file:
                raise FileNotFoundError(f"Archivo de TensorBoard no encontrado en el directorio de logs para el job {job_id}")

            # Si el archivo se encuentra, devuélvelo
            file_path = os.path.join(log_path, tensorboard_file)
            return file_path
                
        except Exception as e:
            logger.error(f"Error al obtener la ruta de TensorBoard para el job {job_id}: {e}")
            raise

    def get_model_path(self, job_id:str):
        """
        Obtiene la ruta del modelo entrenado para el job.
        
        Args:
            job_id (str): El ID del job.
        
        Returns:
            str: La ruta del modelo entrenado.
        """
        try:
            logger.info(f"Obteniendo ruta del modelo para el job {job_id}")
            self.__state_service.set_path(os.path.join(self.__jobs_storage_path,job_id,'logs','state.json'))
            state = self.__state_service.get_state()
            if(state == "WAIT"):
                raise Exception(f"El job {job_id} aún está en ejecución. El modelo estará disponible una vez que el job haya finalizado.")
            elif(state == "RUNNING"):
                model_path = os.path.join(self.__jobs_storage_path, job_id, 'trained_model', 'checkpoints' ,'model_checkpoint_latest.zip')
                if os.path.exists(model_path):
                    return model_path, "checkpoint"
                else:
                    logger.warning(f"No se encontró el modelo para el job {job_id}")
                    return None,"Model not found."
            else:
                model_path = os.path.join(self.__jobs_storage_path, job_id, 'trained_model', 'model.zip')
                if os.path.exists(model_path):
                    return model_path, "final"
                else:
                    raise Exception(f"El job {job_id} no tiene un modelo entrenado.")
                    
        except Exception as e:
            logger.error(f"Error al obtener la ruta del modelo para el job {job_id}: {e}")
            raise
