
from controller import Robot, Motor, Receiver
from Movimientos.HROSbot import *
import math
import numpy as np

class HROSbotComportamental(HROSbot):
    """
        Representa al robot husuario robot con comportamientos definidos.

        Esta clase extiende de HROSbot, heredando de la misma todos los atributos y métodos.
    """

    def __init__(self, bot):
        """
            Inicializa un objeto de tipo HROSbotComportamental.

            Llama al constructor de la clase padre e inicializa atributos que se utilizarán para la definición de comportamientos.

            Args:
                robot (bot): [Robot]
        """
        super().__init__(bot)
        self.exploracion = False
        self.anguloAnterior = 0.5
        self.maximoGiroDerecha = 0.25
        self.maximoGiroIzquierda = 0.25

#-----Comportamientos----- 

    def ir_estimulo(self):
        """
            Busca la señal de un Emmiter y en caso de encontrarla orienta el robot hacia la misma y avanza la distancia que hay entre él y el emisor.

        """
        self.robot.step(self.robotTimestep)
        print("-----> Ir_estimulo")
        velocidad = self.speed
        finaliza = False
        giro = False

        if (self.haySenial()):
            direccion = self.receiver.getEmitterDirection() #1: x; 2: y; 3:z;
            self.actualizarSenial() 
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
                    distancia = self.distanciaSenial()
                    self.vaciarCola()
                    finaliza = self.avanzar(distancia,velocidad)
                    self.actualizarSenial() 
            self.vaciarCola()
            
        return finaliza

#-----

    def evitarObstaculo(self, obstaculo):
        """
            En base a la distancia y el punto de más cercano al obstaculo (pasado por parámetro) gira el robot y avanza hasta que el obstaculo ya no exista.

            Args:
                obstaculo(list) : [Lista de tres elementos. Primer posición: punto del lidar; Segunda posición: lado del obstaculo; Tercera posición: distancia más cercana al obstaculo]
        """
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
            self.actualizarSenial()

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
            self.actualizarSenial()

            while((self.getObstaculoAIzquierda()!=None)and(finaliza)):
                if(self.getObstaculoAlFrente(0.1)==None):
                    finaliza = self.avanzar(0.5,5.0)
                else:
                    finaliza = False  

    def evitarObstaculoGuiado(self):
        """
            Evita un obstaculo girando en dirección a la última señal encontrada.
            En caso de no poder hace un llamado al método evitarObstaculo().
        """
        
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
                    self.actualizarSenial()
                else:
                    giro = self.giroDerecha(0.5*np.pi)
                    self.actualizarSenial()

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
                    self.actualizarSenial()

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
                    self.actualizarSenial()

                    while((self.getObstaculoADerecha()!=None)and(finaliza)):
                        if(self.getObstaculoAlFrente(0.1)==None):
                            finaliza = self.avanzar(0.5,5.0)
                        else:
                            finaliza = False
                        
                        
        self.vaciarCola()
        self.robot.step(self.robotTimestep)
        self.actualizarOrientación(0.0)

#-----

    def explorar(self):
        """
            Explora el entorno decidiendo de forma aleatoria si girar o no. 
            - Si gira, lo hace en base a la ultima señal detectada.
        """
        print("--> Explorar")
        self.robot.step(self.robotTimestep)
        self.vaciarCola()
        velocidad = self.speed
        distancia = 1

        if (not self.haySenial()):
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
                    self.actualizarSenial()

                    if(self.getObstaculoAlFrente()==None):
                        self.avanzar(distancia,velocidad)
                           
            else:
                self.actualizarSenial() 
                self.avanzar(distancia,velocidad)
                   
            self.exploracion=False
            self.vaciarCola()

#----------

#-----Métodos complementarios-----

    def actualizarOrientación(self, angulo):
        """
            Actualiza la orientación del robot.
            Almacena el angulo de giro previo y actualiza el maximo giro que puede realizar.
        """
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
        """
            Determina hacia que lado girar en base al obstaculo y la ultima señal detectada.

            Retorna :
                - 1 si el giro es hacia la izquierda.
                - 2 si el giro es hacia la derecha.
                - 3 si el giro es indeterminado.
            
            Args:
                obstaculo(list) : [Lista de tres elementos. Primer posición: punto del lidar; Segunda posición: lado del obstaculo; Tercera posición: distancia más cercana al obstaculo]
        """
        ultimaSenial = self.get_ultimaSenial()
        if(((obstaculo==None)or(obstaculo[2]>(self.minDistancia-0.1)))and(ultimaSenial!=None)):
            if (ultimaSenial[0]<1):
                if(ultimaSenial[1]>0):
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

#----------