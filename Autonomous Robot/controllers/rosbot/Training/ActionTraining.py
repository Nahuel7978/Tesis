
from abc import ABC, abstractmethod
from Training.TrainingEnvironment import *

class ActionTraining(TrainingEnvironment):

    def __init__(self, recompensaMaxima, recompensaMedia, recompensaMinima, valorPaso, penalizacionMedia, penalizacion, epocas, pasos):
        super().__init__(recompensaMaxima, recompensaMinima, valorPaso, penalizacion, epocas, pasos)
        self.recompensaMedia = recompensaMedia
        self.penalizacionMedia = penalizacionMedia

    
    def determinarRecompensa(self, robot, ejecucion, estadoAnterior, estadoActual, senialAct =0, senialAnt = 0 ,DistSenialAlm=None, AngSenialAlm=None):    
        robot.activateRobotTimestep()
        reconexion = False
        angMejora = 0
        acercamiento = False
        print("senial:",senialAct)
        if(senialAct>0):
            robot.actualizarSenial()
            dist_senial = robot.get_distanciaUltimaSenial()
            angulo_senial = robot.anguloUltimaSenial()
            
            acercamiento=True
            print("SenialAnt==",senialAnt)
            reconexion = (senialAnt==0)
            
            if((DistSenialAlm!=None)and(not reconexion)):
                acercamiento = ((dist_senial+0.5)<DistSenialAlm)
                angMejora = abs(AngSenialAlm)-abs(angulo_senial)
                
        else:
            dist_senial = None
            orient_senial = None
            angMejora=-1

        esquinaAnterior=(estadoAnterior%4==0)
        esquinaAcutal=(estadoActual%4==0)

        obstaculoCercano = [0,1,2,3,12,13,14,15]

        mov = False

        recompensa = 0
        print("alejamiento=((",not reconexion,")and((",dist_senial,"!=None)and((",not acercamiento,")and(",angMejora,"<0))))")#Se aleja o gira de forma erronea.
        print("acercamiento=((",reconexion,")or((",dist_senial,"!=None)and((",acercamiento,")or(",angMejora,">0.5))))")#Se ace
        if(not ejecucion):
            print("INFO: no termino la acción")
            if((acercamiento) or (angMejora>0.5)):
                recompensa = self.recompensaMedia
                print("Pr: ",recompensa,"-- Se acerco o giro en dirección correcta, o se reconecto.")
            else:    
                recompensa= self.penalizacionMaxima
                print("Pr: ",recompensa,"-- No hizo nada.")
        else:
            tolerancia = 0.3 
            alejamiento=((not reconexion)and((dist_senial!=None)and((not acercamiento)and(angMejora<0))))#Se aleja o gira de forma erronea.
            acercamiento=((reconexion)or((dist_senial!=None)and((acercamiento)or(angMejora>0.5))))#Se acerco o giro en dirección correcta, o se reconecto.

            if(robot.estimuloEncontrado(tolerancia)):
                recompensa = self.recompensaMaxima
            
            elif(esquinaAnterior):#Estuvo en una esquina
                print("INFO: Estuvo en una esquina")
                if(esquinaAcutal):#Esta en una esquina
                    recompensa = self.penalizacionMedia
                    print("Pr:",recompensa,"-- Esta en una esquina")

                elif(estadoActual in obstaculoCercano):
                    recompensa = self.recompensaMinima
                    print("Pr: ",recompensa,"-- NO esta en una esquina / obstacaluco cercano")

                else:
                    recompensa = self.recompensaMedia
                    print("Pr:",recompensa,"-- NO esquina / obstaculos Lejos o Via Libre.")

            elif(estadoAnterior in obstaculoCercano): #Obstaculo cercano.
                print("INFO: Estuvo con Obstaculo cercano.")
                if(esquinaAcutal): #Esta en una esquina
                    recompensa = self.penalizacionMedia
                    print("Pr:",recompensa,"-- Esta en una esquina")

                elif(estadoActual in obstaculoCercano): #Sigue con obstaculo cercano
                    recompensa = self.penalizacionMinima
                    print("Pr: ",recompensa,"-- Sigue obstaculo cercano")

                else: #No tiene más un obstaculo cercano.
                    print("INFO: No tiene más un obstaculo cercano.")
                    if(estadoAnterior>11): #señal almacenada
                        print("INFO: tenia una señal almacenada")
                        if(acercamiento):#Se acerco o giro en dirección correcta, o se reconecto.
                            recompensa = self.recompensaMedia
                            print("Pr: ",recompensa,"-- Se acerco o giro en dirección correcta, o se reconecto.")
                        else:
                            recompensa = self.recompensaMinima #Salio del obstaculo cercano
                            print("Pr: ",recompensa,"-- Salio del obstaculo cercano.(Tiene señal almacenada)")
                    else:
                        print("INFO: sin señal almacenada")
                        if(estadoActual>11): #Encuentra una señal
                            recompensa = self.recompensaMedia
                            print("Pr: ",recompensa,"-- Encuentra una señal")
                        else:
                            recompensa = self.recompensaMinima #Salio del obstaculo cercano
                            print("Pr: ",recompensa,"-- Salio del obstaculo cercano.")

            elif((estadoAnterior<=11)): #Obstaculo lejano o via libre sin señal almacedada
                print("INFO: Tenia un Obstaculo lejano o via libre sin señal")
                if(estadoActual>11): #Encuentra una señal
                    recompensa = self.recompensaMinima
                    print("Pr: ",recompensa,"-- Encuentra una señal")
                else:
                    recompensa = self.penalizacionMinima #Sigue con obstaculo lejano o via libre.
                    print("Pr: ",recompensa,"-- Sigue con obstaculo lejano o via libre.")

            elif(estadoAnterior>11): #Obstaculo lejano o via libre con señal

                if((21<=estadoAnterior<=23)or(29<=estadoAnterior<=31)): #Via libre y con señal.
                    print("INFO: tenia Via libre y con señal almacenada. Estado Ant:",estadoAnterior)
                    if(30<=estadoAnterior<=31): #Señal a la derecha, con obstaculo a la izquierda o via libre
                        print("INFO: Señal a la derecha, con obstaculo a la izquierda o via libre. Reconexion:",reconexion)
                        if(alejamiento):#Se aleja o gira de forma erronea.
                            recompensa = self.penalizacionMedia
                            print("Pr: ",recompensa,"-- Se aleja o gira de forma erronea.")
                        
                        elif(acercamiento):#Se acerco o giro en dirección correcta, o se reconecto.
                            recompensa = self.recompensaMedia
                            print("Pr: ",recompensa,"-- Se acerco o giro en dirección correcta, o se reconecto.")

                        elif(angMejora>=0.1):
                            recompensa = self.recompensaMinima
                            print("Pr: ",recompensa,"-- Se giro en dirección correcta pero poco. Ang_mejora:",angMejora)
                        else:
                            recompensa = self.penalizacionMinima
                            print("Pr: ",recompensa,"-- otroCaso: sigue igual")

                    elif((estadoAnterior!=22) or (estadoAnterior!=29)): #Señal a la izquierda, con obstaculo a la derecha o via libre
                        print("INFO: Señal a la izquierda, con obstaculo a la derecha o via libre. Reconexion:",reconexion)
                        if(alejamiento):#Se aleja o gira de forma erronea.
                            recompensa = self.penalizacionMedia
                            print("Pr: ",recompensa,"-- Se aleja o gira de forma erronea.")
                        
                        elif(acercamiento):#Se acerco o giro en dirección correcta, o se reconecto.
                            recompensa = self.recompensaMedia
                            print("Pr: ",recompensa,"-- Se acerco o giro en dirección correcta, o se reconecto.")
                        elif(angMejora>=0.1):
                            recompensa = self.recompensaMinima
                            print("Pr: ",recompensa,"-- Se giro en dirección correcta pero poco. Ang_mejora:",angMejora)
                        else:
                            recompensa = self.penalizacionMinima
                            print("Pr: ",recompensa,"-- otroCaso: sigue igual")

                    else: #Otros casos
                        if(reconexion):
                            recompensa = self.recompensaMinima
                            print("Pr: ",recompensa,"-- otroCaso: reconexion")
                        else:
                            recompensa = self.penalizacionMinima
                            print("Pr: ",recompensa,"-- otroCaso: sigue igual")

                else: #Obstaculo lejano con señal
                    print("INFO: Obstaculo lejano con señal")
                    if((21<=estadoActual<=23)or(29<=estadoActual<=31)): #Actualmente en Via libre
                        print("INFO: Actualmente en Via libre")
                        if(acercamiento):#Se acerco o giro en dirección correcta, o se reconecto.
                            recompensa = self.recompensaMedia    
                            print("Pr: ",recompensa,"-- Se acerco o giro en dirección correcta, o se reconecto.")
                        else:
                            recompensa = self.recompensaMinima    
                            print("Pr: ",recompensa,"-- Salío del obstaculo lejano.")
                    else: #Sigo con obstaculo lejano o cercano.
                        if(estadoActual in obstaculoCercano):
                            if(reconexion):
                                recompensa = self.recompensaMinima
                                print("Pr: ",recompensa,"-- Se acerco a un obstaculo pero hubo reconexion.")    
                            else:
                                recompensa = self.penalizacionMinima
                                print("Pr: ",recompensa,"-- Se acerco a un obstaculo.")
                        elif(acercamiento):
                            recompensa = self.recompensaMinima    
                            print("Pr: ",recompensa,"-- Se acerco o giro en dirección correcta, o se reconecto.")
                        else:
                            if(reconexion):
                                recompensa = self.recompensaMinima
                                print("Pr: ",recompensa,"-- Sigue igual pero hubo reconexion.")    
                            else:
                                recompensa = self.penalizacionMinima
                                print("Pr: ",recompensa,"-- otroCaso: sigue igual")
            else:
                recompensa=self.penalizacionMinima
                print("Pr: ",recompensa,"-- otroCaso: sigue igual")

        print("recompensa: ", recompensa)
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
            estSig = robot.estadoActual_2(1)
            ambSig = robot.get_ambienteActual() 

            siguienteAccion = robot.siguienteAccion(estSig)
            
            antDistSenial = None
            angAnteriorSenial = None

            robot.vaciarCola()
            robot.resetUltimaSenial()
            actSenial = robot.get_receiver()

            if(actSenial>0):
                actDistSenial = robot.distanciaSenial()
                angActualSenial=robot.anguloUltimaSenial()
            else:
                actDistSenial = None
                angActualSenial = None


            while((not objAlcanzado)and(j<=self.pasos)):
                print("----------------------Paso ",j," -|- Epoca ",i,"----------------------------------")
                antSenial = actSenial
                antDistSenial = actDistSenial
                angAnteriorSenial = angActualSenial

                estAct = estSig
                ambAct = ambSig

                accion = siguienteAccion

                print("Estado Actual: ", estAct,". Acción: ",accion)


                ejecucion = robot.ejecutar(accion)

                estSig = robot.estadoActual(accion)
                ambSig = robot.get_ambienteActual()
                siguienteAccion = robot.siguienteAccion(estSig)#estAct
                
                robot.activateRobotTimestep()
                actSenial = robot.get_receiver()
                print("Estado Siguiente: ", estSig,". Acción: ",siguienteAccion)
                
                recompensa = self.determinarRecompensa(robot,ejecucion,ambAct,ambSig,actSenial,antSenial,antDistSenial,angAnteriorSenial)
                
                robot.actualizarPoliticas(estAct,accion,estSig,siguienteAccion,recompensa)

                

                if(actSenial>0):
                    actDistSenial = robot.distanciaSenial()
                    angActualSenial=robot.anguloUltimaSenial()
                else:
                    actDistSenial = None
                    angActualSenial = None

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
