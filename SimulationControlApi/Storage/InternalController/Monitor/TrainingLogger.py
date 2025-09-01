from pathlib import Path


class TrainingLogger:
    
    def __init__(self, log_dir: Path):
        self.__log_dir = log_dir
        self.__log_file = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura el sistema de logging"""
        try:
            self.__log_file = open(self.__log_dir / "train.log", "a", buffering=1)
        except Exception as e:
            print(f"Error al configurar logging: {e}")
            self.__log_file = None
    
    def log(self, *args, level="INFO"):
        """Log unificado a archivo y consola"""
        message = f"[{level}] " + " ".join(str(arg) for arg in args)
        
        # Log a consola
        print(message, flush=True)
        
        # Log a archivo si está disponible
        if self.__log_file:
            print(message, file=self.__log_file, flush=True)
    
    def error(self, *args):
        """Log de errores"""
        self.log(*args, level="ERROR")
    
    def info(self, *args):
        """Log informativo"""
        self.log(*args, level="INFO")
    
    def close(self):
        """Cierra el archivo de log"""
        if self.__log_file:
            self.__log_file.close()

