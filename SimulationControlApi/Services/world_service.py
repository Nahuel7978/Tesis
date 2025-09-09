import os
import json
import zipfile
import shutil
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from Services.core.config import Config
from Services.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class WorldProcessingError(Exception):
    """Excepción personalizada para errores en el procesamiento del mundo"""
    pass

class WorldService:
    """
    Servicio encargado de procesar archivos de mundo de Webots.
    
    Responsabilidades:
    - Crear directorio de trabajo para el job
    - Extraer y validar archivos .zip con mundos de Webots
    - Parchear archivos .wbt para usar InternalController
    - Generar archivo de configuración de entrenamiento
    """
    
    def __init__(self):
        self.__config = Config()
        self.__jobs_storage_path = Path(self.__config.get_storage_path())
        self.__internal_controller_path = Path(self.__config.get_internal_controller_path())
    
    def setup_job_workspace(self, job_id: str) -> Path:
        """
        Crea la estructura de directorios necesaria para un job.
        
        Args:
            job_id: Identificador único del job
            
        Returns:
            Path: Ruta del directorio del job creado
            
        Raises:
            WorldProcessingError: Si no se puede crear el directorio
        """
        job_path = os.path.join(self.__jobs_storage_path, job_id)
        
        try:
            # Crear directorios necesarios
            directories = ['world', 'config', 'logs', 'trained_model']
            for directory in directories:
                job_dir=os.path.join(job_path, directory)
                os.makedirs(job_dir, exist_ok=False)
            
            logger.info(f"Workspace creado para job {job_id} en {job_path}")
            return job_path
            
        except Exception as e:
            logger.error(f"Error creando workspace para job {job_id}: {str(e)}")
            raise WorldProcessingError(f"No se pudo crear el workspace: {str(e)}")
    
    def extract_world_archive(self, zip_file_path: str, job_id: str) -> Path:
        """
        Extrae el archivo ZIP del mundo en el directorio del job.
        
        Args:
            zip_file_path: Ruta al archivo ZIP
            job_id: Identificador del job
            
        Returns:
            Path: Ruta del directorio donde se extrajo el mundo
            
        Raises:
            WorldProcessingError: Si hay problemas con la extracción
        """
        job_path = os.path.join(self.__jobs_storage_path, job_id)
        world_path = os.path.join(job_path, 'world')
        
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                # Validar que el ZIP no esté corrupto
                bad_file = zip_ref.testzip()
                if bad_file:
                    raise WorldProcessingError(f"Archivo ZIP corrupto: {bad_file}")
                
                # Encontrar el nombre de la carpeta raíz dentro del ZIP
                if zip_ref.namelist():
                    first_item = zip_ref.namelist()[0]
                    # Extraer solo el nombre de la carpeta (ej. "autonomo/")
                    if '/' in first_item:
                        extracted_folder_name = first_item.split('/')[0]
                
                if not extracted_folder_name:
                    raise WorldProcessingError("No se pudo determinar la carpeta raíz en el archivo ZIP.")
                
                # Validar nombres de archivos (seguridad)
                for member in zip_ref.infolist():
                    if self._is_unsafe_path(member.filename):
                        raise WorldProcessingError(f"Ruta insegura detectada: {member.filename}")
                
                # Extraer archivos
                zip_ref.extractall(world_path)
                
            extracted_path=os.path.join(world_path, extracted_folder_name)
            logger.info(f"Mundo extraído para job {job_id} en {extracted_path}")
            return extracted_path
            
        except zipfile.BadZipFile:
            logger.error(f"Archivo ZIP inválido para job {job_id}")
            raise WorldProcessingError("El archivo proporcionado no es un ZIP válido")
        except Exception as e:
            logger.error(f"Error extrayendo mundo para job {job_id}: {str(e)}")
            raise WorldProcessingError(f"Error en la extracción: {str(e)}")
    
    def get_robot(self, job_id:str) -> str:
        """
        Obtiene el nombre del robot del archivo de configuración .JSON.
        
        Returns:
            str: Nombre del robot
        """
        config_path = os.path.join(self.__jobs_storage_path, job_id, 'config', 'train_config.json')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            def_robot = config_data.get('def_robot')
            controller = config_data.get('controller')
            env_class = config_data.get('env_class')

            return def_robot, controller, env_class
        except FileNotFoundError:
            logger.error(f"Archivo de configuración no encontrado para job {job_id}")
        except json.JSONDecodeError:
            logger.error(f"Error leyendo archivo de configuración para job {job_id}. JSON no valido")
   
    def validate_world(self,name_robot:str, world_path: Path):
        """
        Valida que el mundo extraído sea válido para Webots.
        
        Args:
            world_path: Ruta del directorio del mundo
            
        Returns:
            WorldValidationResult: Resultado de la validación
        """
        
        try:
            # Buscar archivos .wbt
            wbt_files = list(world_path.rglob("*.wbt"))
            
            if not wbt_files:
                raise WorldProcessingError("No se encontró ningún archivo .wbt en el mundo")
            
            if len(wbt_files) > 1:
                raise WorldProcessingError(f"Se encontraron múltiples archivos .wbt: {[f.name for f in wbt_files]}")
            
            # Usar el primer archivo .wbt encontrado
            world_file = wbt_files[0]
            
            # Validar contenido del archivo .wbt
            robots = self._find_robot_in_wbt(name_robot,world_file)
            
            if not robots:
                raise WorldProcessingError("No se encontró ningún robot ",name_robot," en el archivo .wbt")
            
            # Validar estructura básica
            if not self._validate_wbt_structure(world_file):
                raise WorldProcessingError("Estructura del archivo .wbt inválida.")
            
            logger.info(f"Mundo validado correctamente: {world_file.name}, robots encontrados: {robots}")
            
            return world_file
        except Exception as e:
            logger.error(f"Error validando mundo: {str(e)}")
           
    def patch_world_controllers(self,robot_name:str, world_file_path: str) -> None:
        """
        Parchea el archivo .wbt para que todos los robots usen InternalController.
        
        Args:
            world_file_path: Ruta al archivo .wbt
            
        Raises:
            WorldProcessingError: Si hay problemas con el parcheo
        """
        try:
            world_file = Path(world_file_path)
            
            # Leer contenido original
            with open(world_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Crear backup
            backup_path = world_file.with_suffix('.wbt.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Parchear controladores
            patched_content = self._patch_controllers_in_content(robot_name,content)
            
            # Escribir archivo parcheado
            with open(world_file, 'w', encoding='utf-8') as f:
                f.write(patched_content)
            
            #shutil.rmtree(backup_path, ignore_errors=True)  # Eliminar backup
            logger.info(f"Archivo .wbt parcheado correctamente: {world_file.name}")
            
        except Exception as e:
            logger.error(f"Error parcheando archivo .wbt: {str(e)}")
            raise WorldProcessingError(f"Error en el parcheo: {str(e)}")

    def delete_world(self, job_path:Path):
        world=job_path / "world"
        try:
            if(self._get_world(job_path)==False):
                logger.info("No existe el directorio world para eliminar")
            else:
                shutil.rmtree(world)
                logger.info(f"Directorio world eliminado correctamente: {world}")
        except Exception as e:
            logger.error(f"Error eliminando directorio world: {str(e)}")
            raise WorldProcessingError(f"Error eliminando directorio world: {str(e)}")
        
    def _get_world(self, job_path:Path):
        world=job_path / "world"
        return os.path.exists(world)
    
    def _is_unsafe_path(self, path: str) -> bool:
        """Verifica si una ruta es insegura (path traversal)"""
        return os.path.isabs(path) or ".." in path
    
    def _find_robot_in_wbt(self,robot:str, wbt_file: Path) -> List[str]:
        """
        Busca una definición específica de robot en el archivo .wbt.

        Args:
            robot (str): El nombre del robot a buscar.
            wbt_file (Path): La ruta del archivo .wbt.

        Returns:
            bool: True si el robot es encontrado, False en caso contrario.
        """
        try:
            with open(wbt_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Patrón para capturar robots por DEF, name, o por el tipo de PROTO.
            # Usa re.escape para manejar correctamente caracteres especiales en el nombre.
            # El patrón es "DEF nombre_robot { ... }" o "nombre_robot { ... }" o "name "nombre_robot"".
            pattern = re.compile(
                # Patrón 1: Busca 'DEF nombre_robot Rosbot'
                r'DEF\s+' + re.escape(robot) + r'\s+[\w]+\s*{'
                r'|'
                # Patrón 2: Busca 'name "nombre_robot"'
                r'name\s*"' + re.escape(robot) + r'"'
                r'|'
                # Patrón 3: Busca el tipo de robot (ej. "Elisa3 {")
                r'' + re.escape(robot) + r'\s*{',
                re.MULTILINE | re.DOTALL
            )
            
            # re.search es más eficiente que re.findall para encontrar la primera coincidencia.
            if re.search(pattern, content):
                logger.info(f"El robot '{robot}' fue encontrado en el archivo.")
                return True
                
        except FileNotFoundError:
            logger.error(f"Error: El archivo '{wbt_file}' no fue encontrado.")
        except Exception as e:
            logger.warning(f"Error buscando el robot '{robot}' en {wbt_file}: {str(e)}")
        
        return False
    
    def _validate_wbt_structure(self, wbt_file: Path) -> bool:
        """Valida la estructura básica del archivo .wbt"""
        try:
            with open(wbt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificaciones básicas
            required_elements = ['#VRML', 'WorldInfo', 'Viewpoint']
            return all(element in content for element in required_elements)
            
        except Exception:
            return False
    
    def _patch_controllers_in_content(self, name: str, content: str) -> str:
        """
        Parchea el contenido del archivo .wbt para cambiar el controlador de un robot específico.
        
        Args:
            name (str): El nombre del robot (DEF, name, o tipo de PROTO).
            controller (str): El nombre del controlador actual del robot.
            content (str): El contenido completo del archivo .wbt.

        Returns:
            str: El contenido del archivo .wbt con el controlador actualizado.
        """
        lines = content.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Buscar líneas que contengan el robot específico
            robot_found = False
            
            # Caso 1: DEF robot_name TipoRobot {
            def_pattern = rf'DEF\s+{re.escape(name)}\s+\w+\s*\{{'
            if re.search(def_pattern, line):
                robot_found = True
            
            # Caso 2: TipoRobot { (donde TipoRobot es robot_name)
            elif re.match(rf'{re.escape(name)}\s*\{{', line.strip()):
                robot_found = True
            
            if robot_found:
                # Encontramos el robot, ahora buscar su controlador
                result_lines.append(line)  # Añadir la línea del robot
                i += 1
                brace_count = line.count('{') - line.count('}')
                
                # Procesar el contenido del robot hasta cerrar todas las llaves
                while i < len(lines) and brace_count > 0:
                    current_line = lines[i]
                    
                    # Si encontramos una línea de controller, la reemplazamos
                    if re.search(r'^\s*controller\s*"[^"]*"', current_line):
                        # Mantener la indentación original
                        indent_match = re.match(r'^(\s*)', current_line)
                        indent = indent_match.group(1) if indent_match else '  '
                        current_line = f'{indent}controller "InternalController"'
                    
                    result_lines.append(current_line)
                    brace_count += current_line.count('{') - current_line.count('}')
                    i += 1
            else:
                result_lines.append(line)
                i += 1
        
        return '\n'.join(result_lines)
        
    


if __name__ == "__main__":
    # Ejemplo de uso
    service = WorldService()
    job_id = "job_123"
    path_zip = "/home/roman7978/Documentos/university_portfolio/Tesis/autonomous_robot.zip"
    #service.setup_job_workspace(job_id)
    #extracted=service.extract_world_archive(path_zip, job_id)
    #name,controller,env_class = service.get_robot(job_id)
    #wbt=service.validate_world(name,Path("../Storage/Jobs/job_123/world/Autonomous Robot"))
    #service.patch_world_controllers(name,wbt)
