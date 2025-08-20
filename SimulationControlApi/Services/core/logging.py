import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

class ColorFormatter(logging.Formatter):
    """Formatter que añade colores a los logs en consola"""
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarillo
        'ERROR': '\033[31m',      # Rojo
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Aplicar color al nivel de log
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

class LoggerSetup:
    """Configurador centralizado de logging para toda la aplicación"""
    
    _loggers = {}
    _setup_done = False
    
    @classmethod
    def setup_logging(cls, 
                     log_level: str = "INFO",
                     log_format: Optional[str] = None,
                     log_dir: Optional[str] = None,
                     enable_console: bool = True,
                     enable_file: bool = True) -> None:
        """
        Configura el sistema de logging de la aplicación
        
        Args:
            log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Formato personalizado de logs
            log_dir: Directorio donde guardar archivos de log
            enable_console: Si habilitar logging en consola
            enable_file: Si habilitar logging en archivos
        """
        if cls._setup_done:
            return
        
        # Configuración por defecto
        if log_format is None:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        if log_dir is None:
            log_dir = "./logs"
        
        # Crear directorio de logs
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Configurar el logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Limpiar handlers existentes
        root_logger.handlers.clear()
        
        # Handler para consola
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_level.upper()))
            
            # Usar colores en consola
            if sys.stdout.isatty():  # Solo si es terminal interactivo
                console_formatter = ColorFormatter(log_format)
            else:
                console_formatter = logging.Formatter(log_format)
            
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # Handler para archivo general
        if enable_file:
            # Archivo principal con rotación
            file_handler = logging.handlers.RotatingFileHandler(
                os.path.join(log_dir, "simulation_api.log"),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_formatter = logging.Formatter(log_format)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            
            # Archivo separado para errores
            error_handler = logging.handlers.RotatingFileHandler(
                os.path.join(log_dir, "errors.log"),
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            root_logger.addHandler(error_handler)
        
        # Configurar loggers de librerías externas
        cls._configure_external_loggers()
        
        cls._setup_done = True
        
        # Log de inicio
        logger = logging.getLogger(__name__)
        logger.info(f"Sistema de logging inicializado - Nivel: {log_level}")
    
    @classmethod
    def _configure_external_loggers(cls):
        """Configura el nivel de logging de librerías externas"""
        # Reducir verbosidad de librerías externas
        external_loggers = {
            'urllib3.connectionpool': logging.WARNING,
            'requests.packages.urllib3': logging.WARNING,
            'docker': logging.WARNING,
            'uvicorn.access': logging.WARNING,  # Si usas uvicorn
            'fastapi': logging.INFO,
        }
        
        for logger_name, level in external_loggers.items():
            logging.getLogger(logger_name).setLevel(level)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Obtiene un logger configurado para un módulo específico
        
        Args:
            name: Nombre del logger (normalmente __name__)
            
        Returns:
            logging.Logger: Logger configurado
        """
        if not cls._setup_done:
            cls.setup_logging()
        
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        
        return cls._loggers[name]

def get_logger(name: str) -> logging.Logger:
    """
    Función de conveniencia para obtener un logger
    
    Args:
        name: Nombre del logger (usar __name__)
        
    Returns:
        logging.Logger: Logger configurado
    """
    return LoggerSetup.get_logger(name)

def setup_logging_from_config(config):
    """
    Configura logging usando un objeto Config
    
    Args:
        config: Instancia de Config con configuraciones de logging
    """
    LoggerSetup.setup_logging(
        log_level=getattr(config, 'log_level', 'INFO'),
        log_format=getattr(config, 'log_format', None),
        log_dir=getattr(config, 'log_dir', './logs')
    )

class JobLogger:
    """Logger especializado para jobs específicos"""
    
    @staticmethod
    def create_job_logger(job_id: str, log_dir: str) -> logging.Logger:
        """
        Crea un logger específico para un job
        
        Args:
            job_id: ID del job
            log_dir: Directorio donde guardar los logs del job
            
        Returns:
            logging.Logger: Logger específico del job
        """
        logger_name = f"job.{job_id}"
        logger = logging.getLogger(logger_name)
        
        # Evitar duplicar handlers
        if logger.handlers:
            return logger
        
        # Crear directorio de logs del job
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Handler para archivo del job
        job_handler = logging.FileHandler(
            os.path.join(log_dir, "train.log")
        )
        job_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        job_handler.setFormatter(formatter)
        logger.addHandler(job_handler)
        
        # No propagar al logger padre para evitar duplicados
        logger.propagate = True
        
        return logger

# Funciones de conveniencia para casos específicos
def log_job_start(job_id: str, world_file: str):
    """Log del inicio de procesamiento de un job"""
    logger = get_logger("world_service")
    logger.info(f"Iniciando procesamiento - Job: {job_id}, Mundo: {world_file}")

def log_job_completion(job_id: str, duration_seconds: float):
    """Log de completación de un job"""
    logger = get_logger("world_service")
    logger.info(f"Job completado - ID: {job_id}, Duración: {duration_seconds:.2f}s")

def log_job_error(job_id: str, error: Exception):
    """Log de error en un job"""
    logger = get_logger("world_service")
    logger.error(f"Error en job {job_id}: {str(error)}", exc_info=True)