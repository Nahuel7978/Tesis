
from abc import ABC, abstractmethod
from Training.TrainingEnvironment import *

class BehavioralTraining(TrainingEnvironment):

    def __init__(self, recompensaMaxima, recompensaMinima, valorPaso, penalizacion, epocas, pasos):
        super().__init__(recompensaMaxima, recompensaMinima, valorPaso, penalizacion, epocas, pasos)


    def determinarRecompensa(self, robot, antValPos, antDistSenial, antAngulo=None):
        actValPosDer = round(robot.get_frontRightPositionSensor(), 1)
        actValPosIzq = round(robot.get_frontLeftPositionSensor(), 1)
        senal = robot.get_receiver()
        recompensa = 0
        
        # Verificar movimiento
        movimiento = not ((antValPos[0] + self.toleranciaMovimiento > actValPosIzq) and 
                        (antValPos[1] + self.toleranciaMovimiento > actValPosDer))
        
        if not movimiento:
            print("|-> Recompensa: ",self.penalizacionMaxima)
            return self.penalizacionMaxima
        
        if senal > 0:
            tolerancia = 0.3
            
            # RECOMPENSA MÁXIMA: Meta alcanzada
            if robot.estimuloEncontrado(tolerancia):
                print("|-> Recompensa: ",self.recompensaMaxima)
                return self.recompensaMaxima
            
            # Datos actuales
            actDistSenial = robot.distanciaSenial()
            actAngulo = robot.anguloUltimaSenial()  # Tu método
            
            # 1. Recompensa por acercarse
            if antDistSenial is not None:
                delta_distancia = antDistSenial - actDistSenial
                if delta_distancia > 0:  # Se acercó
                    recompensa += self.recompensaMinima * (1 + delta_distancia)
                else:  # Se alejó
                    recompensa += self.penalizacionMinima * (1 - delta_distancia)
            
            # 2. Recompensa por orientación correcta
            orientacion_robot = robot.get_orientacion_robot()  # Método que implementarás
            
            # Diferencia entre orientación del robot y dirección hacia la señal
            diferencia_angular = abs(orientacion_robot - actAngulo)
            
            # Normalizar a [0, π]
            if diferencia_angular > math.pi:
                diferencia_angular = 2 * math.pi - diferencia_angular
            
            # Recompensa por buena orientación
            if diferencia_angular < math.pi / 6:  # < 30°
                recompensa += 0.2
            elif diferencia_angular < math.pi / 3:  # < 60°
                recompensa += 0.1
            else:  # > 60°
                recompensa -= 0.1
            
            # 3. Recompensa por mejorar orientación
            if antAngulo is not None:
                # Si el ángulo hacia la señal cambió favorablemente
                delta_orientacion = abs(antAngulo - actAngulo)
                if delta_orientacion < 0.1:  # Se mantiene bien orientado
                    recompensa += 0.05
        
        else:
            recompensa = self.penalizacionMinima *0.5
        
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
            antAngulo = None

            if(robot.haySenial()):
                actDistSenial = robot.distanciaSenial()
                antAngulo = robot.anguloUltimaSenial()
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
                siguienteAccion = robot.siguienteAccion(estSig)

                print("Estado Siguiente: ", estAct,". Acción: ",siguienteAccion)

                recompensa = self.determinarRecompensa(robot,antValPos,antDistSenial,antAngulo)
                
                robot.actualizarPoliticas(estAct,accion,estSig,siguienteAccion,recompensa)

                actValPosDer = round(robot.get_frontRightPositionSensor(), 1)
                actValPosIzq = round(robot.get_frontLeftPositionSensor(), 1)

                if(robot.haySenial()):
                    actDistSenial = robot.distanciaSenial()
                    antAngulo = robot.anguloUltimaSenial()
                else:
                    actDistSenial = None
                    antAngulo = None

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
