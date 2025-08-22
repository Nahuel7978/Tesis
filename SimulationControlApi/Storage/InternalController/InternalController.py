import os
import sys
import json
import traceback
import importlib
from pathlib import Path
from typing import Dict, Any, Optional

from stable_baselines3.common.env_checker import check_env
from stable_baselines3 import PPO, DQN, A2C, SAC, TD3
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.logger import configure
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback

#PATHS
WORKSPACE = Path("/workspace")
CONFIG_PATH = os.environ.get("CONFIG_PATH", WORKSPACE / "config" / "train_config.json")
LOG_DIR = WORKSPACE / "logs"
MODEL_DIR = WORKSPACE / "trained_model"
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Agregar workspace al path para imports
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)

class TrainingLogger:
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_file = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura el sistema de logging"""
        try:
            self.log_file = open(self.log_dir / "train.log", "a", buffering=1)
        except Exception as e:
            print(f"Error al configurar logging: {e}")
            self.log_file = None
    
    def log(self, *args, level="INFO"):
        """Log unificado a archivo y consola"""
        message = f"[{level}] " + " ".join(str(arg) for arg in args)
        
        # Log a consola
        print(message, flush=True)
        
        # Log a archivo si está disponible
        if self.log_file:
            print(message, file=self.log_file, flush=True)
    
    def error(self, *args):
        """Log de errores"""
        self.log(*args, level="ERROR")
    
    def info(self, *args):
        """Log informativo"""
        self.log(*args, level="INFO")
    
    def close(self):
        """Cierra el archivo de log"""
        if self.log_file:
            self.log_file.close()

class TrainingController:
    def __init__(self):
        self.logger = TrainingLogger(LOG_DIR)
        self.config = None
        self.env = None
        self.model = None
        self.sb3_logger = None
        
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
            
            self.logger.info("Configuración cargada exitosamente")
            self.logger.info(f"Modelo: {config['model']}")
            self.logger.info(f"Controlador: {config['controller']}")
            self.logger.info(f"Clase del entorno: {config['env_class']}")
            self.logger.info(f"Timesteps: {config['timesteps']}")
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {e}")
            raise
    
    def create_environment(self, config: Dict[str, Any]):
        """Crea e instancia el entorno del usuario"""
        try:
            module_name = config["controller"]
            class_name = config["env_class"]
            
            # Importar el módulo del usuario
            try:
                # Importación directa del módulo
                module = importlib.import_module(f"{module_name}.{module_name}")
                self.logger.info(f"Módulo importado desde {module_name}.{module_name}")
            except ImportError as e:
                raise ImportError(f"No se pudo importar {module_name}: {e}")
            
            # Obtener la clase del entorno
            if not hasattr(module, class_name):
                raise AttributeError(f"La clase '{class_name}' no existe en el módulo '{module_name}'")
            
            EnvClass = getattr(module, class_name)
            
            # Instanciar el entorno
            env = EnvClass()
            
            # Envolver con Monitor para logging adicional
            env = Monitor(env, str(LOG_DIR / "monitor"))
            
            self.logger.info("Entorno creado exitosamente")
            return env
            
        except Exception as e:
            self.logger.error(f"Error al crear entorno: {e}")
            raise
    
    def validate_environment(self, env):
        """Valida que el entorno sea compatible con Stable-Baselines3"""
        try:
            check_env(env, warn=True)
            self.logger.info("Entorno validado exitosamente")
        except Exception as e:
            self.logger.error(f"Error en validación del entorno: {e}")
            raise
    
    def create_model(self, config: Dict[str, Any], env):
        """Crea el modelo de RL según la configuración"""
        try:
            model_name = config["model"]
            policy = config["policy"]
            model_params = config.get("model_params", {})
            
            # Mapeo de modelos disponibles
            model_map = {
                "PPO": PPO,
                "DQN": DQN, 
                "A2C": A2C,
                "SAC": SAC,
                "TD3": TD3
            }
            
            if model_name not in model_map:
                raise ValueError(f"Modelo no soportado: {model_name}. Modelos disponibles: {list(model_map.keys())}")
            
            ModelClass = model_map[model_name]
            
            # Configurar logger de SB3
            self.sb3_logger = configure(str(LOG_DIR), ["stdout", "tensorboard"])
            
            # Crear modelo con parámetros
            self.logger.info(f"Parámetros del modelo: {model_params}")
            model = ModelClass(policy, env, **model_params)
            model.set_logger(self.sb3_logger)
            
            self.logger.info("Modelo creado exitosamente")
            return model
            
        except Exception as e:
            self.logger.error(f"Error al crear modelo: {e}")
            raise
    
    def setup_callbacks(self, config: Dict[str, Any]):
        """Configura callbacks para el entrenamiento"""
        callbacks = []
        
        # Checkpoint callback para guardar modelo periódicamente
        checkpoint_callback = CheckpointCallback(
            save_freq=max(1000, int(config["timesteps"]) // 10),
            save_path=str(MODEL_DIR / "checkpoints"),
            name_prefix="model_checkpoint"
        )
        callbacks.append(checkpoint_callback)
        
        return callbacks
    
    def train_model(self, config: Dict[str, Any]):
        """Ejecuta el entrenamiento del modelo"""
        try:
            timesteps = int(config["timesteps"])
            self.logger.info(f"Iniciando entrenamiento por {timesteps} timesteps")
            
            # Configurar callbacks
            callbacks = self.setup_callbacks(config)
            
            # Entrenar modelo
            self.model.learn(
                total_timesteps=timesteps,
                tb_log_name="robot_training",
                callback=callbacks
            )
            
            self.logger.info("Entrenamiento completado exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error durante el entrenamiento: {e}")
            raise
    
    def save_model(self):
        """Guarda el modelo entrenado"""
        try:
            model_path = MODEL_DIR / "model.zip"
            self.model.save(str(model_path))
            self.logger.info(f"Modelo guardado en: {model_path}")
            
            # Guardar también configuración usada
            config_save_path = MODEL_DIR / "training_config.json"
            with open(config_save_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuración guardada en: {config_save_path}")
            
        except Exception as e:
            self.logger.error(f"Error al guardar modelo: {e}")
            raise
    
    def cleanup(self):
        """Limpieza de recursos"""
        try:
            if self.env:
                self.env.close()
                self.logger.info("Entorno cerrado")
        except Exception as e:
            self.logger.error(f"Error al cerrar entorno: {e}")
        
        finally:
            self.logger.close()
    
    def run(self):
        """Método principal que ejecuta todo el pipeline de entrenamiento"""
        try:
            # Cargar configuración
            self.config = self.load_config()
            
            # Crear entorno
            self.env = self.create_environment(self.config)
            
            # Validar entorno
            self.validate_environment(self.env)
            
            # Crear modelo
            self.model = self.create_model(self.config, self.env)
            
            # Entrenar modelo
            self.train_model(self.config)
            
            # Guardar modelo
            self.save_model()
            
            self.logger.info("Pipeline de entrenamiento completado exitosamente")
            return 0
            
        except Exception as e:
            self.logger.error("Error crítico en el pipeline de entrenamiento:")
            self.logger.error(str(e))
            self.logger.error(traceback.format_exc())
            return 1
            
        finally:
            self.cleanup()

def main():
    """Función principal"""
    controller = TrainingController()
    exit_code = controller.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()