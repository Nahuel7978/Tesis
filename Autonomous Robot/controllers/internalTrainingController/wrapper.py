import gym
import threading
import traceback # Importar traceback

class TimeoutWrapper(gym.Wrapper):
    def __init__(self, env, timeout_seconds=10):
        #, path_register=None
        super().__init__(env)
        self.__timeout_seconds = timeout_seconds
        #self.__path_register = path_register
        
    def step(self, action):
        """
        Ejecuta step con timeout usando threading (compatible con Windows y Unix)
        """
        result = [None]  # Lista para poder modificar desde el hilo
        exception = [None]
        
        def real_step():
            try:
                result[0] = self.env.step(action)
            except Exception as e:
                exception[0] = e
        
        # Crear y iniciar hilo
        thread = threading.Thread(target=real_step)
        thread.daemon = True
        thread.start()
        
        # Esperar con timeout
        thread.join(timeout=self.__timeout_seconds)
        
        if thread.is_alive():
            # Timeout ocurrió
            print(f"[WARNING] Timeout en step ({self.__timeout_seconds}s) - terminando episodio")
            
            try:
                obs = self.env.reset()
                return obs, -10.0, False, {"timeout": True, "timeout_seconds": self.__timeout_seconds}
            except Exception as e:
                print(f"[ERROR] Falló en reset: {e}")
                raise
        
        # Si hay excepción en el hilo, relanzarla
        if exception[0] is not None:
            exc_type, exc_value, exc_traceback = exception[0]
            raise exc_type.with_traceback(exc_traceback)
            
        return result[0]
        

