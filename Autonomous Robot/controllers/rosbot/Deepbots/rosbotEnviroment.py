
from deepbots.supervisor.controllers.csv_supervisor_env import CSVSupervisorEnv
import numpy as np
from gym.spaces import Box,Discrete
from controller import Robot, Camera, Motor, Receiver, Supervisor


class RobotEnviroment(CSVSupervisorEnv):
    def __init__(self,observation_space=0, action_space=0):
        super().__init__("TrainingEmitter","TrainingReceiver")
        self.observation_space = Box(low=-np.inf, high=np.inf, shape=(observation_space,), dtype=np.float32)
        self.action_space = Discrete(action_space)
        self.obs_space = observation_space
        self.act_space= action_space

        self.message_received = None
        self.reward = 0
        self.done = False

        self.supervisor = Supervisor()
        self.robot_node = self.supervisor.getFromDef("principal_robot")
        self.translation = self.robot_node.getField("translation")
        self.rotation = self.robot_node.getField("rotation")
        self.startPoints = []
        self.startRotation = []

    def get_observations(self):
        self.message_received = self.handle_receiver()
        if self.message_received is not None:
            message = np.array(self.message_received[:-2], dtype=np.float32).tolist()
            self.reward = int(self.message_received[-2])
            self.done = bool(self.message_received[-1])
            if(not self.done):
                self.startPoints.append(self.currentLocation())
                self.startRotation.append(self.currentRotation())

            return message
        else:
            return self.get_default_observation()

    def get_default_observation(self):
        return np.zeros(self.obs_space, dtype=np.float32)
    
    def get_reward(self, action):
        return self.reward
    
    def is_done(self):
        return self.done

    def get_info(self):
        """
        This method can be implemented to return any diagnostic
        information on each step, e.g. for debugging purposes.
        """
        return {"reward": self.reward, "done": self.done}
    
    def reset(self):
        index = np.random.randint(0,len(self.startPoints))
        self.translation.setSFVec3f(self.startPoints[index])
        self.rotation.setSFRotation(self.startRotation[index])
        super().reset()
        return self.get_observations()
    

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