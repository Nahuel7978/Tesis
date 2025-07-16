
from controller import Robot, Motor, Receiver
from Movimientos.HROSbot import *
import math
import numpy as np

class BehavioralHROSbot(HROSbot):
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
        velocidad = self.speedMax
        finaliza = False
        giro = False

        giro = self.giroSenial()
        print("giro: ",giro)
        if(giro):
            finaliza = self.avanzarSenial()
            
        self.vaciarCola()
            
        return finaliza

#-----
    def evitarObstaculo(self):
        """
            Evita un obstaculo girando en dirección a la última señal encontrada.
            En caso de no poder hacerlo evita el obstaculo en base al angulo del obstaculo encontrado.
        """
        
        self.robot.step(self.robotTimestep)
        self.vaciarCola()
        print("--> Evitar Obstaculo")
        obstaculo =  self.getObstaculoAlFrente(0.3)
        giro = False
        finaliza = False

        if((obstaculo != None)or((self.get_frontLeftSensor()<self.minDistancia)or(self.get_frontRightSensor()<self.minDistancia))):
            self.retroceder(0.05,2)
            
            if(self.get_ultimaSenial()!=None):
                giro = self.giroParaleloObstaculoGuiado()

            if(not giro):
                giro = self.giroParaleloObstaculo()
                
            if(giro):
                finaliza = self.avanzarParaleloObstaculo()
            else:
                finaliza = False

        self.vaciarCola()
        self.robot.step(self.robotTimestep)
        return finaliza

#-----

    def explorar(self):
        """
            Explora el entorno decidiendo de forma aleatoria si girar o no. 
            - Si gira, lo hace en base a la ultima señal detectada.
        """
        print("--> Explorar")
        self.robot.step(self.robotTimestep)
        self.vaciarCola()
        velocidad = self.speedMax
        distancia = 1

        ##if (not self.haySenial()):
        self.exploracion = True
        probMov = np.random.uniform()
        giro = False
        avance = False

        if((probMov<=0.7)):
            gDeterminado = self.orientacionUltimaSenial()
            i = 0
            while((not giro)and(i<=1)):
                i +=1
                if(gDeterminado==1):
                    self.robot.step(self.robotTimestep)
                    giro = self.giroAleatorioIzquierda()
                   
                    if(not giro):
                        gDeterminado = 2
                else:
                    self.robot.step(self.robotTimestep)
                    giro = self.giroAleatorioDerecha()

                    if(not giro):
                        gDeterminado = 1
                           
        if(probMov<=0.3):
            distancia=2

        avance = self.avanzar(distancia,velocidad) 
        
        self.exploracion=False

        return (giro or avance)

#----------

#----------