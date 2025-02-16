
from abc import ABC, abstractmethod
from Training.TrainingEnvironment import *

class BehavioralTraining(TrainingEnvironment):

    def __init__(self, recompensaMaxima, recompensaMinima, valorPaso, penalizacion, epocas, pasos):
        super().__init__(recompensaMaxima, recompensaMinima, valorPaso, penalizacion, epocas, pasos)


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
                actDistSenial = robot.distanciaSenial()
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
