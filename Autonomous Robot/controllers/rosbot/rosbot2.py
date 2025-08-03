from stable_baselines3 import DQN
from stable_baselines3.common.env_checker import check_env
from Deepbots.rosbotController import *
from controller import Robot, Motor, Receiver, Supervisor
from Deepbots.wrapper import Wrapper
import numpy as np
import math
import time
 
# Crear entorno

env = RobotController()

"""
for i in range(5):  # Ignorar los primeros 5 pasos del simulador
    env.activateRobotTimestep()
"""
def trainAgent(env):
   # wrapped_env = Wrapper(env, timeout_seconds=10)
    try:
        #check_env(env, warn=True)

        # Crear el modelo
        model = DQN(
            "MlpPolicy",
            env,
            verbose=1,
            learning_rate=0.0005,
            buffer_size=25000,
            learning_starts=500,
            batch_size=32,
            gamma=0.99,
            train_freq=4,
            target_update_interval=500,
            exploration_fraction=0.1,
            exploration_final_eps=0.02,
        )

        TIMESTEPS = 10000
        model.learn(total_timesteps=TIMESTEPS)

        # Guardar el modelo entrenado
        model.save("rosbot_model.zip")

        #wrapped_env.close()
        env.close()

    except Exception as e:
        print(f"Error al crear el modelo: {e}")
        return None

#trainAgent(env)

#env.explorar()
#env.detener()
#print(env.reward())
#print(env.create_message())
#env.explorar()
#env.detener()
#print(env.create_message())
#env.evitarObstaculo()
#env.ir_estimulo()
#env.detener()
#env.avanzar(1,3)
#env.avanzarParaleloObstaculo()
#env.evitarObstaculo()

