import numpy as np
import matplotlib.pyplot as plt
from Qlearning.AdaptiveHROSbot import *
from abc import ABC, abstractmethod
from controller import Supervisor

class TrainingEnvironment(ABC):
    """
        Representa un entorno de entrenamiento para un algoritmo de Q-learning.
    """
    def __init__(self, recompensaMaxima, recompensaMinima, valorPaso, penalizacion, epocas, pasos):
        """
            Inicializa el objeto del tipo EntornoEntrenamiento.

            Args:
                recompensaMaxima(int) : [Recompensa máxima que puede recibir un agente en su entrenamiento]
                recompensaMinima(int) : [Recompensa máxima que puede recibir un agente en su entrenamiento]
                valorPaso(int) : [Valor que sumará el agente en cada paso]
                penalizacion(int) : [Penalización que recibirá el agente ante un fallo]
                epocas(int) : [Cantidad total de epocas de entrenamiento]
                pasos(int) : [Cantidad de pasos que realizará el agente]
        """
        self.recompensaMaxima = recompensaMaxima
        self.recompensaMinima = recompensaMinima
        self.penalizacionMaxima = penalizacion
        self.penalizacionMinima = valorPaso

        self.epocas = epocas
        self.pasos = pasos

        self.supervisor = Supervisor()
        self.robot_node = self.supervisor.getFromDef("principal_robot")
        self.timestep = int(self.supervisor.getBasicTimeStep())
        self.translation = self.robot_node.getField("translation")
        self.rotation = self.robot_node.getField("rotation")

        self.toleranciaMovimiento = 1

        self.registroEntrenamiento = []

#------

#-----Entrenamiento-----
    @abstractmethod
    def determinarRecompensa(self, robot,antValPos, antDistSenial):
        """
            Determina la recompensa que recibirá el agente en base a su movimientos previos y distancia al objetivo.

            Args:
                robot(bot) : [Robot]
                antValPos(List) : [Lista de tres posiciones con los ultimo valor de posición]
                antDistSenial(float) : [Ultimo valor de distancia al objetivo]
        """
        pass

#-----
    @abstractmethod
    def entrenamiento(self, robot):
        """
           Entrena un número determinado de epocas al agente, permitiendole al mismo avanzar una cantidad determinadas de pasos

           Args:
                robot(bot) : [Robot]
        """
        pass
#-----

    def visualizarRegistroEntrenamiento(self):
        """
            Visualiza en un gráfico el proceso de entrenamiento.
        """
        epocas = [lista[0] for lista in self.registroEntrenamiento]
        pasos = [lista[1] for lista in self.registroEntrenamiento]

        plt.figure(figsize=(10, 5))
        plt.plot(epocas, pasos, marker='o', linestyle='-', color='b')
        plt.title('Pasos por Época')
        plt.xlabel('Épocas')
        plt.ylabel('Pasos')
        plt.grid(True)
        plt.show()
#-----

#----Ubicación y Rotación------

    def ubicacionActual(self):
        """
            Retorna la ubicación exácta del agente dentro del simulador.
        """
        self.supervisor.step(self.timestep) 
        return self.translation.getSFVec3f()

#-----

    def rotacionActual(self):
        """
            Retorna la rotación exácta del agente dentro del simulador.
        """
        self.supervisor.step(self.timestep) 
        return self.rotation.getSFRotation()

#-----

    def puntoInicial(self,posicionesInicial, rotacionesInicial):
        """
            Ubica al agente dentro del entorno en base a un conjunto de posiciones y rotaciones iniciales.

            Retorna el indice de la posición en la cual se encuentra el agente.

            Args:
                posicionesInicial(List) : [Lista de n posiciones que almacena las diferentes posiciones iniciales]
                rotacionesInicial(List) : [Lista de n posiciones que almacena las diferentes rotaciones iniciales]
        """
        index = np.random.randint(0,len(posicionesInicial))
        self.translation.setSFVec3f(posicionesInicial[index])
        self.rotation.setSFRotation(rotacionesInicial[index])
        self.supervisor.simulationResetPhysics()
        return index

#-----

    def get_toleranciaMovimiento(self):
        """
            Retorna el atributo toleranciaMovimiento de la clase.
        """
        return self.toleranciaMovimiento

#-----

    def set_toleranciaMovimiento(self, value):
        """
            Actualiza el valor de toleranciaMovimiento.

            Args:
                value(float) : [Nuevo valor de tolerancia al movimiento]
        """
        self.toleranciaMovimiento = value

#----------
