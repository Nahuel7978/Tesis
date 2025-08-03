
from controller import Robot, Camera, Motor, Receiver, Supervisor
from deepbots.supervisor.controllers.csv_supervisor_env import CSVSupervisorEnv
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.logger import configure
import os
from monitor import ResourceMonitor
import datetime

import numpy as np
from gym.spaces import Box,Discrete
from stable_baselines3 import DQN


class RobotEnviroment(CSVSupervisorEnv):
    def __init__(self,obs_space=0, act_space=0):
        super().__init__()
        self.observation_space = Box(low=-np.inf, high=np.inf, shape=(obs_space,), dtype=np.float32)
        self.action_space = Discrete(act_space)
        self.obs_space = obs_space
        self.act_space= act_space

        self.message_received = None
        self.reward = 0
        self.done = 'False'

        self.robot_node = self.getFromDef("principal_robot")
        if self.robot_node is None:
            raise RuntimeError("No se encontró el robot con DEF='principal_robot'")
        
        self.translation = self.robot_node.getField("translation")
        self.rotation = self.robot_node.getField("rotation")
        self.startPoints = []
        self.startRotation = []
        self.startPoints.append(self.currentLocation())
        self.startRotation.append(self.currentRotation())

    def get_observations(self):
        self.message_received = self.handle_receiver()
        if self.message_received is not None:
            message = np.array(self.message_received[:-2], dtype=np.float32).tolist()
            self.reward = float(self.message_received[-2])
            self.done = self.message_received[-1]
            if(self.done=='False'):
                self.startPoints.append(self.currentLocation())
                self.startRotation.append(self.currentRotation())
            return np.array(message, dtype=np.float32)
        else:
            return self.get_default_observation()

    def get_default_observation(self):
        return np.zeros(self.obs_space, dtype=np.float32)
    
    def get_reward(self, action):
        return self.reward
    
    def is_done(self):
        if((self.done=='True')or((self.message_received is not None)and(self.message_received[-1] == 'True'))):
            self.done = 'True'
            return True
        else:
            return False

    def step(self, action):
        self.handle_emitter(action)
        if super(Supervisor, self).step(self.timestep) == -1:
            exit()
        
        self.vaciarCola()  # Vaciar la cola del receiver
        while self.receiver.getQueueLength() <= 0:
            super(Supervisor, self).step(self.timestep)
             
        return (
            self.get_observations(),
            self.get_reward(action),
            self.is_done(),
            self.get_info(),
        )
    
    def get_info(self):
        """
        This method can be implemented to return any diagnostic
        information on each step, e.g. for debugging purposes.
        """
        return {"reward": self.reward, "done": self.done}
    
    def reset(self):
        
        if(self.is_done()==True):
            index = np.random.randint(0,len(self.startPoints))
            self.translation.setSFVec3f(self.startPoints[index])
            self.rotation.setSFRotation(self.startRotation[index])
            self.done='False'
            self.handle_emitter(self.act_space) # Enviar acción de reinicio
            self.simulationResetPhysics()
            super(Supervisor, self).step(int(self.getBasicTimeStep()))
            return self.get_default_observation()

        return self.get_observations()
    
    def render(self, mode="human"):
        pass
    
    def handle_emitter(self, action):
        iterable_action = [int(action)]
        super().handle_emitter(iterable_action)

        

    def vaciarCola(self):
        """
        Vacia la cola del receiver que contiene todos los paquetes recibidos hasta el momento.
        """
        while(self.receiver.getQueueLength() > 0):
            self.receiver.nextPacket()
#----Ubicación y Rotación------

    def currentLocation(self):
        """
            Retorna la ubicación exácta del agente dentro del simulador.
        """
        return self.translation.getSFVec3f()

#-----

    def currentRotation(self):
        """
            Retorna la rotación exácta del agente dentro del simulador.
        """
        return self.rotation.getSFRotation()
    
#---------------

#--------Main--------
def trainAgent(env):
   # wrapped_env = Wrapper(env, timeout_seconds=10)
    monitor = ResourceMonitor(f"./train_result/3-training_resources.txt", monitoring_interval=1.0)
    try:
        log_dir = "./train_logs/"
        os.makedirs(log_dir, exist_ok=True)

        # Env con Monitor para registrar métricas adicionales (recompensas, etc.)
        monitored_env = Monitor(env)

        # Configurar el logger para escribir logs compatibles con TensorBoard
        new_logger = configure(log_dir, ["stdout", "tensorboard"])

        # Crear el modelo
        model = DQN(
            "MlpPolicy",
            monitored_env,
            verbose=2,
            learning_rate=0.0005,
            buffer_size=25000,
            learning_starts=500,
            batch_size=32,
            gamma=0.99,
            train_freq=4,
            target_update_interval=500,
            exploration_fraction=0.1,
            exploration_final_eps=0.02,
            tensorboard_log=log_dir
        )

        model.set_logger(new_logger)

        monitor.start_monitoring()

        TIMESTEPS = 10000
        model.learn(total_timesteps=TIMESTEPS, tb_log_name="dqn_rosbot")

        # Guardar el modelo entrenado
        model.save("./train_result/3-rosbot_model.zip")

    except Exception as e:
        print(f"Error al crear el modelo: {e}")
        return None
    
    finally:
        monitor.stop_monitoring()
        env.close()
    

#------------

#env = RobotEnviroment(obs_space=403, act_space=3)
#check_env(env, warn=True)
#trainAgent(env)
"""
model = DQN.load("./train_result/rosbot_model.zip", env=env)

obs = env.reset()
done = False
while not done:
    action, _states = model.predict(obs)
    obs, reward, done, info = env.step(action)
    #env.render()
"""

"""
print(env.step(1))
print("----")
print(env.step(1))
print("----")
print(env.step(1))
print("----")

print(env.step(1))
print("----")
env.reset()
print(env.step(2))
print(env.step(1))

"""