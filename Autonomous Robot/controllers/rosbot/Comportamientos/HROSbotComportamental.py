
from controller import Robot, Motor, Receiver
from Movimientos.HROSbot import *
import math
import numpy as np

class HROSbotComportamental(HROSbot):

    def __init__(self, bot):
        super().__init__(bot)
        self.exploracion = False
        self.anguloAnterior = 0.5
        self.maximoGiroDerecha = 0.25
        self.maximoGiroIzquierda = 0.25
        
    def ir_estimulo(self):
        #Detecta la señal e intenta dirigirse a ella. 
        self.robot.step(self.robotTimestep)
        print("-----> Ir_estimulo")
        velocidad = self.speed
        finaliza = False
        giro = False

        if (self.haySeñal()):
            direccion = self.receiver.getEmitterDirection() #1: x; 2: y; 3:z;
            self.actualizarSeñal() 
            if (direccion[0]<1):
                if(direccion[1]>0):
                    self.robot.step(self.robotTimestep)
                    if(self.getObstaculoAIzquierda()==None):
                        giro = self.giroIzquierda(math.atan2(direccion[1], direccion[0]))
                else:
                    self.robot.step(self.robotTimestep)
                    if(self.getObstaculoADerecha()==None):
                        giro = self.giroDerecha(math.atan2(direccion[1], direccion[0]))

                if(giro):
                    self.actualizarOrientación(math.atan2(direccion[1], direccion[0]))
                    distancia = self.distanciaSeñal()
                    self.vaciarCola()
                    finaliza = self.avanzar(distancia,velocidad)
                    self.actualizarSeñal() 
            self.vaciarCola()
            self.robot.step(self.robotTimestep)

        return finaliza

#------
   
#----
    def evitarObstaculo(self, obstaculo):
        #Evita el obstaculo.
        print("-----> Evitar Obstaculo")
        self.robot.step(self.robotTimestep)
        self.vaciarCola()
        angulo = self.getPuntoEnRadianes(obstaculo[0])
        finaliza = True
        metrosReversa = 1
        mt = 0
        retrocedio=True

        if (obstaculo[1] == "right"):
            giro = self.giroIzquierda(angulo) 
            while((not giro)and(retrocedio)and(metrosReversa>mt)):
                retrocedio = self.retroceder(0.05,5.0)
                mt+=0.05
                giro = self.giroIzquierda(angulo)
                if((not giro)and(mt>=metrosReversa)):
                    self.giroDerecha(-angulo)

            nuevoObstaculo = self.getObstaculoAlFrente()
            while((nuevoObstaculo !=None)and(giro)):
                self.vaciarCola()
                giro = self.giroIzquierda(self.getPuntoEnRadianes(nuevoObstaculo[0]))
                self.robot.step(self.robotTimestep)
                nuevoObstaculo = self.getObstaculoAlFrente()

            self.robot.step(self.robotTimestep)
            self.actualizarSeñal()

            while((self.getObstaculoADerecha()!=None)and(finaliza)):
                if(self.getObstaculoAlFrente(0.1)==None):
                    finaliza = self.avanzar(0.5,5.0)  
                else:
                    finaliza = False  
            # Obstáculo en frente-izquierda
        elif (obstaculo[1] == "left"):
            giro = self.giroDerecha(-angulo)

            while((not giro)and(retrocedio)and(metrosReversa>mt)):
                retrocedio = self.retroceder(0.05,5.0)
                mt+=0.05
                giro = self.giroDerecha(-angulo)
                if((not giro)and(mt>=metrosReversa)):
                    self.giroIzquierda(angulo)

            nuevoObstaculo = self.getObstaculoAlFrente()
        
            while((nuevoObstaculo !=None)and (giro)):
                self.vaciarCola()
                giro = self.giroDerecha(-self.getPuntoEnRadianes(nuevoObstaculo[0]))
                self.robot.step(self.robotTimestep)
                nuevoObstaculo = self.getObstaculoAlFrente()

            self.robot.step(self.robotTimestep)
            self.actualizarSeñal()

            while((self.getObstaculoAIzquierda()!=None)and(finaliza)):
                if(self.getObstaculoAlFrente(0.1)==None):
                    finaliza = self.avanzar(0.5,5.0)
                else:
                    finaliza = False  

    def evitarObstaculoGuiado(self):
        #Evita un obstaculo girando para donde este la última señal. En caso de no poder llama a evitarObstaculo()
        self.robot.step(self.robotTimestep)
        self.vaciarCola()
        print("--> Evitar Obstaculo Guiado")
        obstaculo =  self.getObstaculoAlFrente()

        # Obstáculo en frente-derecha
        # si el obstáculo está en frente derecha doblo a la izquierda
        if(obstaculo != None):
            #angulo = self.getAnguloDeGiro(obstaculo[0],goal_index)
            angulo = self.getPuntoEnRadianes(obstaculo[0])
            
            gDeterminado = self.determinarGiroAleatorio(obstaculo)
            finaliza = True
        
            if(obstaculo[0]==0):
                if((gDeterminado==1) or (gDeterminado==3)):
                    giro = self.giroIzquierda(0.5*np.pi)
                    self.actualizarSeñal()
                else:
                    giro = self.giroDerecha(0.5*np.pi)
                    self.actualizarSeñal()

                if(not giro):
                    self.evitarObstaculo(obstaculo)
                    
            elif(gDeterminado==2): #giro a la derecha
                if (obstaculo[1] == "right"):    
                    retrocedio = self.retroceder(0.1,2.0)
                    giro = self.giroDerecha(-angulo)
                else:
                    giro = self.giroDerecha(-angulo)

                if(not giro):
                    self.evitarObstaculo(obstaculo)
                else:
                    self.robot.step(self.robotTimestep)
                    nuevoObstaculo = self.getObstaculoAlFrente(0.1)
                    
                    while((nuevoObstaculo !=None)and (giro)):
                        self.vaciarCola()
                        giro = self.giroDerecha(-self.getPuntoEnRadianes(nuevoObstaculo[0]))
                        self.robot.step(self.robotTimestep)
                        nuevoObstaculo = self.getObstaculoAlFrente(0.1)

                    self.robot.step(self.robotTimestep)
                    self.actualizarSeñal()

                    while((self.getObstaculoAIzquierda()!=None)and(finaliza)):
                        if(self.getObstaculoAlFrente(0.1)==None):
                            finaliza = self.avanzar(0.5,5.0)
                        else:
                            finaliza = False   
            elif(gDeterminado==1):
                if(obstaculo[1]=="left"):
                    retrocedio = self.retroceder(0.1,2.0)
                    giro = self.giroIzquierda(angulo)
                else:
                    giro = self.giroIzquierda(angulo)    
                
                if(not giro):
                    self.evitarObstaculo(obstaculo)
                else:
                    self.robot.step(self.robotTimestep)
                    nuevoObstaculo = self.getObstaculoAlFrente(0.1)

                    while((nuevoObstaculo !=None)and(giro)):
                        self.vaciarCola()
                        giro = self.giroIzquierda(self.getPuntoEnRadianes(nuevoObstaculo[0]))
                        self.robot.step(self.robotTimestep)
                        nuevoObstaculo = self.getObstaculoAlFrente(0.1)
                    
                    self.robot.step(self.robotTimestep)
                    self.actualizarSeñal()

                    while((self.getObstaculoADerecha()!=None)and(finaliza)):
                        if(self.getObstaculoAlFrente(0.1)==None):
                            finaliza = self.avanzar(0.5,5.0)
                        else:
                            finaliza = False
                        
                        
        self.vaciarCola()
        self.robot.step(self.robotTimestep)
        self.actualizarOrientación(0.0)
#-----
#----
    def explorar(self):
        #Explora el entorno. Si gira, lo hace en base a la ultima señal detectada
        print("--> Explorar")
        self.robot.step(self.robotTimestep)
        self.vaciarCola()
        velocidad = self.speed
        distancia = 1

        if (not self.haySeñal()):
            self.exploracion = True
            probMov = np.random.uniform()
            obstaculo = self.getObstaculoAlFrente()
            giro = False

            if((probMov<=0.35)):
                gDeterminado = self.determinarGiroAleatorio(obstaculo)
                i = 0
                while((not giro)and(i<=1)):
                    i +=1
                    if(gDeterminado==1):
                        angulo = np.random.uniform(low=0, high=self.maximoGiroIzquierda)
                        self.robot.step(self.robotTimestep)
                        giro = self.giroIzquierda(angulo*np.pi)
                       
                        if(giro):
                            self.actualizarOrientación(angulo)
                        else:
                            gDeterminado = 2
                    else:
                        angulo = -1*np.random.uniform(low=0, high=self.maximoGiroDerecha)
                        self.robot.step(self.robotTimestep)

                        if(self.getObstaculoADerecha()==None):
                            giro = self.giroDerecha(angulo*np.pi)
                        
                        if(giro):
                            self.actualizarOrientación(angulo)
                        else:
                            gDeterminado = 1
                if(giro):
                    self.actualizarSeñal()

                    if(self.getObstaculoAlFrente()==None):
                        self.avanzar(distancia,velocidad)
                           
            else:
                self.actualizarSeñal() 
                self.avanzar(distancia,velocidad)
                   
            self.exploracion=False
            self.vaciarCola()
            self.robot.step(self.robotTimestep)

    def actualizarOrientación(self, angulo):
    #Actualiza la orientación del robot.
        if(self.exploracion):
            anguloActual=angulo+self.anguloAnterior
            self.maximoGiroIzquierda=self.maximoGiroIzquierda-angulo
            self.maximoGiroDerecha= anguloActual
            self.anguloAnterior=anguloActual
        else:
            self.anguloAnterior = 0.5
            self.maximoGiroDerecha = 0.25
            self.maximoGiroIzquierda = 0.25

    

    def determinarGiroAleatorio(self, obstaculo):
    #Determina que giro tomar en base a la señal.
        ultimaSeñal = self.get_ultimaSeñal()
        if(((obstaculo==None)or(obstaculo[2]>(self.minDistancia-0.1)))and(ultimaSeñal!=None)):

            if (ultimaSeñal[0]<1):
                if(ultimaSeñal[1]>0):
                    giro = 1 # 1 = izquierda
                else:
                    giro = 2 #2 = derecha
            else:
                giro=3
        elif(obstaculo!=None):
            if(obstaculo[1]=="right"):
                giro = 1
            else: 
                giro = 2
        else:
            giro = 3 #3 = indeterminado

        print("Giro determinado: ", giro)
        return giro

