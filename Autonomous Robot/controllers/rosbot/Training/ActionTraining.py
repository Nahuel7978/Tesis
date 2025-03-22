
from abc import ABC, abstractmethod
from Training.TrainingEnvironment import *

class ActionTraining(TrainingEnvironment):

    def __init__(self, recompensaMaxima, recompensaMedia, recompensaMinima, valorPaso, penalizacionMedia, penalizacion, epocas, pasos):
        super().__init__(recompensaMaxima, recompensaMinima, valorPaso, penalizacion, epocas, pasos)
        self.recompensaMedia = recompensaMedia
        self.penalizacionMedia = penalizacionMedia

    def determinarRecompensa(self, robot, ejecucion, antDistSenial):
        senal = robot.get_receiver()
        recompensa =  0
        movimiento = False

        if(not ejecucion):
            recompensa = self.penalizacionMaxima
        else:
            movimiento = True

        if(senal>0):
            tolerancia = 0.3 
            if(robot.estimuloEncontrado(tolerancia)):
                recompensa = self.recompensaMaxima

            elif(movimiento):
                actDistSenial = robot.distanciaSenial()

                if((antDistSenial==None)):
                    recompensa = self.recompensaMinima

                elif((antDistSenial<actDistSenial)):
                    recompensa = self.penalizacionMinima

                elif(antDistSenial+tolerancia>actDistSenial):
                    recompensa = self.recompensaMedia
                
        elif(antDistSenial!=None):
            recompensa = self.penalizacionMedia

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
            estSig = robot.estadoActual(0)
            siguienteAccion = robot.siguienteAccion(estSig)
            
            antDistSenial = None
            if(robot.haySenial()):
                actDistSenial = robot.distanciaSenial()
            else:
                actDistSenial = None

            robot.vaciarCola()
            robot.resetUltimaSenial()

            while((not objAlcanzado)and(j<=self.pasos)):
                print("----------------------Paso ",j," -|- Epoca ",i,"----------------------------------")

                antDistSenial = actDistSenial

                estAct = estSig
                accion = siguienteAccion

                print("Estado Actual: ", estAct,". Acción: ",accion)


                ejecucion = robot.ejecutar(accion)

                estSig = robot.estadoActual(accion)
                siguienteAccion = robot.siguienteAccion(estSig)#estAct

                print("Estado Siguiente: ", estSig,". Acción: ",siguienteAccion)

                recompensa = self.determinarRecompensa(robot,ejecucion,antDistSenial)
                
                robot.actualizarPoliticas(estAct,accion,estSig,siguienteAccion,recompensa)


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
