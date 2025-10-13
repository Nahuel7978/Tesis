import os
import sys
import subprocess
import json
import traceback
import importlib
from pathlib import Path
from typing import Dict, Any, Optional


from stable_baselines3.common.env_checker import check_env
from stable_baselines3 import PPO, DQN, A2C, SAC, TD3, DDPG
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.logger import configure
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback

current_dir = Path(__file__).parent
monitor_path = str(current_dir / "Monitor")
wrapper_path = str(current_dir / "Wrapper")
callback_path = str(current_dir / "Callback")

if monitor_path not in sys.path:
    sys.path.insert(0, monitor_path)

if wrapper_path not in sys.path:
    sys.path.insert(0, wrapper_path)

if callback_path not in sys.path:
    sys.path.insert(0, callback_path)

from TrainingLogger import TrainingLogger
from MetricsCapture import MetricsCapture
from StreamInterceptor import StreamInterceptor
from state_service import StateService
from TimeoutWrapper import TimeoutWrapper
from Overwrite import OverwriteCheckpointCallback


#PATHS
WORKSPACE = Path("/workspace")
CONFIG_PATH = os.environ.get("CONFIG_PATH", WORKSPACE / "config" / "train_config.json")
LOG_DIR = WORKSPACE / "logs"
STATE_DIR = LOG_DIR / "state.json"
MODEL_DIR = WORKSPACE / "trained_model"
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Agregar workspace al path para imports
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)

class TrainingController:
    def __init__(self, limit_step):
        self.__logger = TrainingLogger(LOG_DIR)
        self.__state = StateService(STATE_DIR)
        self.__config = None
        self.__env = None
        self.__model = None
        self.__sb3_logger = None
        self.__original_stdout = None
        self.__limit_step = limit_step
        

    def setup_metrics_capture(self):
        """Configura la captura de métricas de entrenamiento"""
        try:
            # Crear directorio de logs si no existe
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            
            # Archivo JSONL para métricas
            jsonl_file = LOG_DIR / "training_metrics.jsonl"
            
            # Interceptar stdout
            self.__original_stdout = sys.stdout
            sys.stdout = StreamInterceptor(self.__original_stdout, MetricsCapture(jsonl_file))
            
            self.__logger.info(f"Captura de métricas configurada. Archivo: {jsonl_file}")
            
        except Exception as e:
            msg=f"Error al configurar captura de métricas: {e}"
            self.__logger.error(msg)
            self.__state.set_state(2, str(msg))
            raise
    
    def restore_stdout(self):
        """Restaura stdout original"""
        if self.__original_stdout:
            sys.stdout = self.__original_stdout

    def load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo JSON"""
        try:
            
            if not CONFIG_PATH.exists():
                raise FileNotFoundError(f"Archivo de configuración no encontrado: {CONFIG_PATH}")
            
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            
            required_fields = ["def_robot","controller", "env_class", "model", "policy", "timesteps"]
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                raise ValueError(f"Campos requeridos faltantes en configuración: {missing_fields}")
            
            self.__logger.info("Configuración cargada exitosamente")
            self.__logger.info(f"Modelo: {config['model']}")
            self.__logger.info(f"Controlador: {config['controller']}")
            self.__logger.info(f"Clase del entorno: {config['env_class']}")
            self.__logger.info(f"Timesteps: {config['timesteps']}")
            
            return config
            
        except Exception as e:
            msg=f"Error al cargar configuración: {e}"
            self.__logger.error(msg)
            self.__state.set_state(2, str(msg))
            raise
    
    def create_environment(self):
        """Crea e instancia el entorno del usuario"""
        try:
            module_name = self.__config["controller"]
            class_name = self.__config["env_class"]
            
            # Importar el módulo del usuario
            try:
                # Importación directa del módulo
                module = importlib.import_module(f"{module_name}.{module_name}")
                self.__logger.info(f"Módulo importado desde {module_name}.{module_name}")
            except ImportError as e:
                raise ImportError(f"No se pudo importar {module_name}: {e}")
            
            # Obtener la clase del entorno
            if not hasattr(module, class_name):
                raise AttributeError(f"La clase '{class_name}' no existe en el módulo '{module_name}'")
            
            EnvClass = getattr(module, class_name)
            
            # Instanciar el entorno
            env = EnvClass()
            
            # Envolver con TimeoutWrapper para manejar tiempo del step.
            env = TimeoutWrapper(env, timeout_seconds=self.__limit_step )

            # Envolver con Monitor para logging adicional
            env = Monitor(env, str(LOG_DIR / "monitor"))
            
            self.__logger.info("Entorno creado exitosamente")
            return env
            
        except Exception as e:
            msg = f"Error al crear entorno: {e}"
            self.__logger.error(msg)
            self.__state.set_state(2, str(msg))
            raise
    
    def validate_environment(self):
        """Valida que el entorno sea compatible con Stable-Baselines3"""
        try:
            env = self.__env
            check_env(env, warn=True)
            self.__logger.info("Entorno validado exitosamente")
        except Exception as e:
            msg = f"Error de validación del entorno: {e}"
            self.__logger.error(msg)
            self.__state.set_state(2, str(msg))
            raise
    
    def create_model(self):
        """Crea el modelo de RL según la configuración"""
        try:
            model_name = self.__config["model"]
            policy = self.__config["policy"]
            model_params = self.__config.get("model_params", {})
            
            # Mapeo de modelos disponibles
            model_map = {
                "PPO": PPO,
                "DQN": DQN, 
                "A2C": A2C,
                "SAC": SAC,
                "TD3": TD3,
                "DDPG": DDPG,
            }
            
            if model_name not in model_map:
                raise ValueError(f"Modelo no soportado: {model_name}. Modelos disponibles: {list(model_map.keys())}")
            
            ModelClass = model_map[model_name]
            
            # Configurar logger de SB3
            self.__sb3_logger = configure(str(LOG_DIR), ["stdout", "tensorboard"])
            
            # Crear modelo con parámetros
            self.__logger.info(f"Parámetros del modelo: {model_params}")
            env=self.__env
            model = ModelClass(policy, env, **model_params)
            model.set_logger(self.__sb3_logger)
            
            self.__logger.info("Modelo creado exitosamente")
            return model
            
        except Exception as e:
            msg = f"Error al crear modelo: {e}"
            self.__logger.error(msg)
            self.__state.set_state(2, str(msg))
            raise
    
    def setup_callbacks(self):
        """Configura callbacks para el entrenamiento"""
        
        callbacks = []
        if(self.__config != None):     
            # Checkpoint callback para guardar modelo periódicamente
            checkpoint_callback = OverwriteCheckpointCallback(
                save_freq=max(1000, int(self.__config["timesteps"]) // 10),
                save_path=str(MODEL_DIR / "checkpoints"),
                name_prefix="model_checkpoint"
            )
            callbacks.append(checkpoint_callback)
        
        return callbacks
    
    def train_model(self):
        """Ejecuta el entrenamiento del modelo"""
        try:
            timesteps = int(self.__config["timesteps"])
            self.__logger.info(f"Iniciando entrenamiento por {timesteps} timesteps")
            
            # Configurar callbacks
            callbacks = self.setup_callbacks()
            
            # Entrenar modelo
            self.__model.learn(
                total_timesteps=timesteps,
                tb_log_name="robot_training",
                callback=callbacks
            )
            
            self.__logger.info("Entrenamiento completado exitosamente")
            
        except Exception as e:
            msg = f"Error durante el entrenamiento: {e}"
            self.__logger.error(msg)
            self.__state.set_state(2, str(msg))
            raise
    
    def save_model(self):
        """Guarda el modelo entrenado"""
        try:
            model_path = MODEL_DIR / "model.zip"
            self.__model.save(str(model_path))
            self.__logger.info(f"Modelo guardado en: {model_path}")
            
            # Guardar también configuración usada
            config_save_path = MODEL_DIR / "training_config.json"
            with open(config_save_path, "w", encoding="utf-8") as f:
                json.dump(self.__config, f, indent=2)
            self.__logger.info(f"Configuración guardada en: {config_save_path}")
            
        except Exception as e:
            self.__logger.error(f"Error al guardar modelo: {e}")
            raise
    
    def cleanup(self):
        """Limpieza de recursos"""        
        subprocess.run(["pkill", "-f", "webots"], check=False)
        try:
            if self.__env:
                self.__env.close()
                self.__logger.info("Entorno cerrado")
        except Exception as e:
            self.__logger.error(f"Error al cerrar entorno: {e}")
        
        finally:
            self.__logger.close()
    
    def run(self):
        """Método principal que ejecuta todo el pipeline de entrenamiento"""
        try:
            
            self.__state.set_state(1)  # Estado RUNNING

            self.setup_metrics_capture()

            self.__config = self.load_config()
        
            self.__env = self.create_environment()
            
            self.validate_environment()
            
            self.__model = self.create_model()
            
            self.train_model()
            
            self.save_model()

            self.cleanup()
            
            self.__state.set_state(3)  # Estado READY
            self.__logger.info("Pipeline de entrenamiento completado exitosamente")
            return 0
            
        except Exception as e:
            self.__logger.error("Error crítico en el pipeline de entrenamiento:")
            self.__logger.error(str(e))
            self.__state.set_state(2, str(e))
            self.__logger.error(traceback.format_exc())
            return 1
            
        finally:
            self.cleanup()

def main():
    controller = TrainingController(30)
    exit_code = controller.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()