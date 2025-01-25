import numpy as np
import matplotlib.pyplot as plt
from Qlearning.AdaptiveHROSbot import *
from controller import Supervisor

class EntornoEntrenamiento():
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

    def determinarRecompensa(self, robot,antValPos, antDistSenial):
        """
            Determina la recompensa que recibirá el agente en base a su movimientos previos y distancia al objetivo.

            Args:
                robot(bot) : [Robot]
                antValPos(List) : [Lista de tres posiciones con los ultimo valor de posición]
                antDistSenial(float) : [Ultimo valor de distancia al objetivo]
        """
        actValPosDer = round(robot.get_frontRightPositionSensor(), 1)
        actValPosIzq = round(robot.get_frontLeftPositionSensor(), 1)
        senal = robot.get_receiver()
        recompensa =  0
        movimiento = False

        if((antValPos[0]+self.toleranciaMovimiento>actValPosIzq) and
           (antValPos[1]+self.toleranciaMovimiento>actValPosDer)):
             recompensa = self.penalizacionMaxima
        else:
            movimiento=True

        if(senal>0):
            tolerancia = 0.3 
            if(robot.estimuloEncontrado(tolerancia)):
                recompensa = self.recompensaMaxima
            elif(movimiento):
                actDistSenial = robot.distanciaSenial()
                if((antDistSenial==None)or(antDistSenial>actDistSenial)):
                    recompensa = self.recompensaMinima
                else:
                    recompensa = self.penalizacionMinima        
        
        elif(movimiento):
            recompensa = self.penalizacionMinima

        print("|--> Recompensa: ", recompensa)
        return recompensa

#-----

    def entrenamiento(self, robot):
        """
           Entrena un número determinado de epocas al agente, permitiendole al mismo avanzar una cantidad determinadas de pasos

           Args:
                robot(bot) : [Robot]
        """
        puntos_partida = []
        rotacion_partida = []
        puntos_partida.append(self.ubicacionActual())
        rotacion_partida.append(self.rotacionActual())

        puntoPartida = 0
        
        for i in range(self.epocas):
            print("|----------------------Epoca ",i,"----------------------------------|")
            objAlcanzado=False
            j = 0
            estSig = robot.estadoActual()
            siguienteAccion = robot.siguienteAccion(estSig)
            antValPos= [0,0]
            actValPosDer = round(robot.get_frontRightPositionSensor(),1)
            actValPosIzq = round(robot.get_frontLeftPositionSensor(), 1) 
            
            antDistSenial = None
            if(robot.haySenial()):
                actDistSenial = robot.distanciaSenial()
            else:
                actDistSenial = None

            robot.vaciarCola()
            robot.resetUltimaSenial()

            while((not objAlcanzado)and(j<=self.pasos)):
                print("----------------------Paso ",j,"----------------------------------")
                antValPos[0] = actValPosIzq
                antValPos[1] = actValPosDer

                antDistSenial = actDistSenial

                estAct = estSig
                accion = siguienteAccion

                print("Estado Actual: ", estAct,". Acción: ",accion)


                robot.ejecutar(accion)

                estSig = robot.estadoActual()
                siguienteAccion = robot.siguienteAccion(estAct)

                print("Estado Siguiente: ", estAct,". Acción: ",siguienteAccion)

                recompensa = self.determinarRecompensa(robot,antValPos,antDistSenial)
                
                robot.actualizarPoliticas(estAct,accion,estSig,siguienteAccion,recompensa)

                actValPosDer = round(robot.get_frontRightPositionSensor(), 1)
                actValPosIzq = round(robot.get_frontLeftPositionSensor(), 1)

                if(robot.haySenial()):
                    actDistSenial = robot.distanciaSenial()
                else:
                    actDistSenial = None

                j += 1
                if(recompensa == self.recompensaMaxima):
                    objAlcanzado = True

            if(not objAlcanzado):
                puntos_partida.append(self.ubicacionActual())
                rotacion_partida.append(self.rotacionActual())

            if(puntoPartida == 0):
                self.registroEntrenamiento.append([i,j])

            puntoPartida = self.puntoInicial(puntos_partida,rotacion_partida)
            robot.resetUltimaSenial()

        del puntos_partida[1:]
        del rotacion_partida[1:]
        self.puntoInicial(puntos_partida,rotacion_partida)
        robot.guardarPoliticas()

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
