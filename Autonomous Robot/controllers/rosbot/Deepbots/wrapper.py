import gym
import signal

class Wrapper(gym.Wrapper):
    def __init__(self, env, timeout_seconds=10):
        super().__init__(env)
        self.timeout_seconds = timeout_seconds
    
    def timeout_handler(self, signum, frame):
        raise TimeoutError("Step timeout")
    
    def step(self, action):
        # Configurar timeout
        signal.signal(signal.SIGALRM, self.timeout_handler)
        signal.alarm(self.timeout_seconds)
        
        try:
            result = self.env.step(action)
            signal.alarm(0)  # Cancelar timeout
            return result
        except TimeoutError:
            signal.alarm(0)
            print("[WARNING] Timeout en step - terminando episodio")
            # Retornar estado terminal con reward negativo
            obs = self.env.get_observations()  # O el último estado conocido
            return obs, -10.0, True, {"timeout": True}
        except Exception as e:
            signal.alarm(0)
            raise e
        

