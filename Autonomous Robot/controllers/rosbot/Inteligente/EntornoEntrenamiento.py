import numpy as np
import matplotlib.pyplot as plt
from Inteligente.HROSbotInteligente import *
from controller import Supervisor

class EntornoEntrenamiento():

    def __init__(self, recompensaMaxima, recompensaMinima, valorPaso, penalizacion, epocas, pasos):

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

    def determinarRecompensa(self, robot,antValPos, antDistSenial):
        
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
                actDistSenial = robot.distanciaSeñal()
                if((antDistSenial==None)or(antDistSenial>actDistSenial)):
                    recompensa = self.recompensaMinima
                else:
                    recompensa = self.penalizacionMinima        
        
        elif(movimiento):
            recompensa = self.penalizacionMinima

        print("|--> Recompensa: ", recompensa)
        return recompensa

    def entrenamiento(self, robot):
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
            if(robot.haySeñal()):
                actDistSenial = robot.distanciaSeñal()
            else:
                actDistSenial = None

            robot.vaciarCola()
            robot.resetUltimaSeñal()

            while((not objAlcanzado)and(j<=self.pasos)):
                print("----------------------Paso ",j,"----------------------------------")
                antValPos[0] = actValPosIzq
                antValPos[1] = actValPosDer

                antDistSenial = actDistSenial

                estAct = estSig
                accion = siguienteAccion

                print("Estado Actual: ", estAct,". Acción: ",accion)


                robot.ejecutarComportamiento(accion)

                estSig = robot.estadoActual()
                siguienteAccion = robot.siguienteAccion(estAct)

                print("Estado Siguiente: ", estAct,". Acción: ",siguienteAccion)

                recompensa = self.determinarRecompensa(robot,antValPos,antDistSenial)
                
                robot.actualizarPoliticas(estAct,accion,estSig,siguienteAccion,recompensa)

                actValPosDer = round(robot.get_frontRightPositionSensor(), 1)
                actValPosIzq = round(robot.get_frontLeftPositionSensor(), 1)

                if(robot.haySeñal()):
                    actDistSenial = robot.distanciaSeñal()
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
            robot.resetUltimaSeñal()

        del puntos_partida[1:]
        del rotacion_partida[1:]
        self.puntoInicial(puntos_partida,rotacion_partida)
        robot.guardarPoliticas()



    def ubicacionActual(self):
        self.supervisor.step(self.timestep) 
        return self.translation.getSFVec3f()

    def rotacionActual(self):
        self.supervisor.step(self.timestep) 
        return self.rotation.getSFRotation()

    def puntoInicial(self,posicionesInicial, rotacionesInicial):
        index = np.random.randint(0,len(posicionesInicial))
        self.translation.setSFVec3f(posicionesInicial[index])
        self.rotation.setSFRotation(rotacionesInicial[index])
        self.supervisor.simulationResetPhysics()
        return index
    
    def get_toleranciaMovimiento(self):
        return self.toleranciaMovimiento

    def set_toleranciaMovimiento(self, value):
        self.toleranciaMovimiento = value

    def visualizarRegistroEntrenamiento(self):
        epocas = [lista[0] for lista in self.registroEntrenamiento]
        pasos = [lista[1] for lista in self.registroEntrenamiento]

        plt.figure(figsize=(10, 5))
        plt.plot(epocas, pasos, marker='o', linestyle='-', color='b')
        plt.title('Pasos por Época')
        plt.xlabel('Épocas')
        plt.ylabel('Pasos')
        plt.grid(True)
        plt.show()

