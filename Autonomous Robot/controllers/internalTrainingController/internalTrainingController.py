from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.logger import configure
import os
import datetime

import numpy as np
from gym.spaces import Box,Discrete
from stable_baselines3 import DQN, PPO, A2C
from wrapper import TimeoutWrapper

import sys
import os

# Agregar el directorio controllers al path
controllers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..','..')
sys.path.append(controllers_path)

from controllers.robotController.robotController import RobotController

def trainAgent(env):
   # wrapped_env = Wrapper(env, timeout_seconds=10)
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
            buffer_size=25000, #
            learning_starts=500, #
            batch_size=32,
            gamma=0.99,
            train_freq=4, #
            target_update_interval=500,#
            exploration_fraction=0.1,#
            exploration_final_eps=0.02,#
            tensorboard_log=log_dir
        )

        model.set_logger(new_logger)

        TIMESTEPS = 10000
        model.learn(total_timesteps=TIMESTEPS, tb_log_name="dqn_rosbot")

        # Guardar el modelo entrenado
        model.save("./train_result/3-rosbot_model.zip")

    except Exception as e:
        print(f"Error al crear el modelo: {e}")
        env.close()
        sys.exit(0)
    
    finally:
        env.close()
        sys.exit(0)
    

#------------
print("Entrenando agente...")
env = RobotController()
wrapped_env = TimeoutWrapper(env, timeout_seconds=10)
wrapped_env.step(2)
#trainAgent(env)
#check_env(env, warn=True)
