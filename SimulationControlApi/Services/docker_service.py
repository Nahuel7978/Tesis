import docker
import os
from pathlib import Path
import logging

# Nombre de la imagen Docker
IMAGE_NAME = "webots_image" 

logger = logging.getLogger(__name__)

class DockerService:
    def __init__(self):
        """
        Inicializa el servicio de Docker.

        Args:
            image_name: Nombre de la imagen de Docker a utilizar para las simulaciones.
        """
        self.__image_name = IMAGE_NAME
        try:
            # Crear cliente de Docker
            self.__client = docker.from_env()
        except docker.errors.DockerException:
            logger.error("Error: No se pudo conectar con Docker.")
            raise
        
        BASE_DIR = Path(__file__).parent.parent  # Directorio del proyecto
        self.__service =(BASE_DIR / "Services" / "state_service.py").resolve()
        self.__jobs_storage_path = (BASE_DIR / "Storage" / "Jobs").resolve()
        self.__internal_controller_path = (BASE_DIR / "Storage" / "InternalController").resolve()

    def start_simulation_for_job(self, job_id: str, world_file_abs_path: Path):
        """
        Levanta un contenedor Docker y ejecuta una simulación de Webots para un job específico.

        Args:
            job_id: El ID del job a ejecutar.
            world_file_abs_path: La ruta absoluta al archivo .wbt que se debe ejecutar.

        Returns:
            True si se inició correctamente, o None si hubo un error.
        """
        container_name = f"webots_job_{job_id}"
        logger.info(f"Iniciando simulación para el job {job_id} en el contenedor {container_name}")

        # Limpiar contenedores previos.
        try:
            old_container = self.__client.containers.get(container_name)
            logger.warning(f"Contenedor previo '{container_name}' encontrado. Deteniendo y eliminando...")
            old_container.stop()
            old_container.remove()
        except docker.errors.NotFound:
            pass  # Es el escenario ideal, no hay contenedor previo.
        except docker.errors.APIError as e:
            logger.error(f"Error de la API de Docker al intentar limpiar contenedor previo: {e}")
            raise

        # Definición de rutas y volúmenes
        host_job_path = self.__jobs_storage_path / job_id
        print(f"host_job_path: {host_job_path}")
        
        # El directorio 'world' del job que contiene el mundo extraído
        host_world_dir = host_job_path / "world"
        print(f"host_world_dir: {host_world_dir}")
        
        # Ruta del .wbt relativa a la carpeta 'world' del job
        world_file_relative_path = world_file_abs_path.relative_to(host_world_dir)
        print(f"world_file_relative_path: {world_file_relative_path}")

        # Ruta del .wbt que se usará dentro del contenedor
        container_wbt_path = Path("/workspace/world") / world_file_relative_path
        print(f"container_wbt_path: {container_wbt_path}")

        # El controlador 'InternalController' se monta en el subdirectorio 'controllers'.
        container_project_root = Path("/workspace/world") / world_file_relative_path.parts[0]
        container_controller_dir = container_project_root / "controllers" / "InternalController"
        monitor_controller_dir = container_controller_dir / "Monitor" / "state_service.py"

        print(f"container_controller_dir: {container_controller_dir}")

        volumes = {
            str(host_world_dir): {
                'bind': '/workspace/world',
                'mode': 'rw'
            },
            str(host_job_path / "logs"): {
                'bind': '/workspace/logs',
                'mode': 'rw'
            },
            str(host_job_path / "trained_model"): {
                'bind': '/workspace/trained_model',
                'mode': 'rw'
            },
            str(host_job_path / "config"): {
                'bind': '/workspace/config',
                'mode': 'ro'
            },
            str(self.__internal_controller_path): {
                'bind': str(container_controller_dir),
                'mode': 'rw'
            },
            str(self.__service):{
                'bind': str(monitor_controller_dir),
                'mode': 'ro'
            }

        }

        # Comandos y variables de entorno
        # xvfb-run es una utilidad que simplifica el uso de Xvfb para aplicaciones headless.
        command = f"""bash -c '
                        echo "Configurando entorno..."
                        mkdir -p /tmp/webots_home/.local/share/applications
                        mkdir -p /tmp/webots_home/.config/Cyberbotics
                        mkdir -p /tmp/.X11-unix
                        chmod 1777 /tmp/.X11-unix
                        
                        find /workspace/world -name "*" -path "*/controllers/*" -type f -exec chmod +x {{}} \;

                        echo "Iniciando Xvfb..."
                        Xvfb :99 -screen 0 1280x1024x24 -ac +extension GLX +render -noreset &
                        sleep 3
                        
                        echo "Verificando OpenGL..."
                        DISPLAY=:99 glxinfo | head -10 || echo "Sin aceleración OpenGL"

                        webots --no-rendering --batch --mode=fast --stdout --stderr "{container_wbt_path}"'
                   """

        # Variables de entorno.
        environment = {
            "USER": os.getenv("USER", "default"),
            "USERNAME": os.getenv("USER", "default"),
            "HOME": "/tmp/webots_home",
            "XDG_RUNTIME_DIR": "/tmp/runtime-webotsuser",
            "DISPLAY": ":99", #En un contenedor Docker sin pantalla física, Xvfb crea una pantalla virtual (normalmente :99 o :1)
            "QT_X11_NO_MITSHM": "1",
            "QT_QPA_PLATFORM": "xcb",#Webots usa Qt, y necesita especificar cómo comunicarse con el servidor X (Xvfb)
            
            **({#GPU
                "LIBGL_ALWAYS_INDIRECT": "0",
                "DRI_PRIME": "1",
            } if self._has_gpu_support() else { #CPU
                "LIBGL_ALWAYS_SOFTWARE": "1",
                "GALLIUM_DRIVER": "llvmpipe",
            }),
            "MESA_GL_VERSION_OVERRIDE": "3.3",
            #"MESA_GLSL_VERSION_OVERRIDE": "130",
            #"MESA_NO_ERROR": "1",
            "PYTHONPATH": "/workspace" #El contenedor tendrá /workspace en el Python path
        }

        #Ejecución del contenedor
        try:
            logger.info(f"Creando y ejecutando contenedor '{container_name}' con imagen '{self.__image_name}'...")
            container_arg = {
                "image":self.__image_name,
                "name":container_name,
                "command":command,
                "network_mode":"bridge",
                "working_dir":"/workspace",
                "volumes":volumes,
                "environment":environment,
                "user":f"{os.getuid()}:{os.getgid()}",  # Ejecuta como usuario actual para evitar problemas de permisos
                "detach":True,
                "tty":True,
                "stdout":True,
                "stderr":True
            }

            """ El hardware de mi PC es viejo para esto
            if self._has_gpu_support():
                container_arg["devices"] = [
                    "/dev/dri:/dev/dri:rwm",
                    "/dev/dri/renderD128:/dev/dri/renderD128:rwm"
                ]
                # También agregar privilegios:
                container_arg["privileged"] = False
                container_arg["cap_add"] = ["SYS_ADMIN"]
            """

            container = self.__client.containers.run(**container_arg)    
            
            return f"Contenedor '{container_name}' (ID: {container.id}) iniciado exitosamente."
        except docker.errors.ImageNotFound:
            logger.error(f"La imagen de Docker '{self.__image_name}' no fue encontrada.")
            raise
        except docker.errors.ContainerError as e:
            logger.error(f"Error dentro del contenedor '{container_name}': {e}")
            raise
        except docker.errors.APIError as e:
            logger.error(f"Error en la API de Docker al iniciar el contenedor: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al iniciar la simulación para el job {job_id}: {e}")
            raise

    def stop_simulation(self, job_id: str) -> bool:
        """Detiene y elimina el contenedor asociado a un job."""
        container_name = f"webots_job_{job_id}"
        try:
            container = self.__client.containers.get(container_name)
            logger.info(f"Deteniendo contenedor '{container_name}'...")
            container.stop()
            container.remove()
            logger.info(f"Contenedor '{container_name}' detenido y eliminado.")
            return True
        except docker.errors.NotFound:
            logger.warning(f"No se encontró el contenedor '{container_name}' para detener.")
            return False
        except docker.errors.APIError as e:
            logger.error(f"Error de la API de Docker al detener el contenedor '{container_name}': {e}")
            return False

    def list_running_simulations(self):
        """Lista los contenedores Docker que están ejecutando simulaciones."""
        try:
            containers = self.__client.containers.list(filters={"name": "webots_job_"})
            running_jobs = [container.name for container in containers]
            logger.info(f"Contenedores en ejecución: {running_jobs}")
            return running_jobs
        except docker.errors.APIError as e:
            logger.error(f"Error de la API de Docker al listar contenedores: {e}")
            return []

    
    def _has_gpu_support(self):
        """Verifica si el sistema tiene soporte GPU"""
        try:
            import subprocess
            result = subprocess.run(['glxinfo', '-B'], capture_output=True, text=True)
            return "direct rendering: Yes" in result.stdout
        except:
            return False

"""
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    docker_service = DockerService()
    base_dir = Path(__file__).parent.parent 
    pt= (base_dir / "Storage/Jobs/job_1/world/Autonomous Robot/worlds/Autonomous Robot.wbt").resolve()
    #docker_service.start_simulation_for_job("job_1", pt)
    docker_service.stop_simulation("job_1")
"""