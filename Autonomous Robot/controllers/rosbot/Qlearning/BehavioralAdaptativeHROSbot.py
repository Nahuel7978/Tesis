
from abc import ABC, abstractmethod
from Qlearning.AdaptiveHROSbot import *

class BehavioralAdaptativeHROSbot(AdaptiveHROSbot, BehavioralHROSbot):

    def __init__(self, bot, l_rate, t_descuento, r_exploracion):
        AdaptiveHROSbot.__init__(self, bot, l_rate, t_descuento, r_exploracion)
        self.putCantidadAcciones(3)
        self.putCantidadEstados(13)
        self.inicializarPoliticas()

    def ejecutar(self, accion):
        """
        Ejecuta el comportamiento correspondiente basado en la acción especificada.

        Args:
            accion (int): Código de la acción a ejecutar:
                0 - ir hacia el estímulo
                1 - evitar obstáculos
                2 - explorar el entorno

        Raises:
            ValueError: Si la acción no está dentro del rango permitido.
        """
        ejecucion = False
        if(accion==0):
            ejecucion = self.ir_estimulo()
        elif(accion==1):
            ejecucion = self.evitarObstaculo()
        elif(accion==2):
            ejecucion = self.explorar()
        else:
            raise ValueError(f"Acción no válida: {accion}")


    def estadoActual(self, acc=None):
        indice = 0
        distacia = 3
        self.robot.step(self.robotTimestep)
        #--Parámetros
        of = self.getObstaculoAlFrente()
        fls =self.frontLeftSensor.getValue() 
        frs = self.frontRightSensor.getValue()
        Queque = self.receiver.getQueueLength()
        if(Queque>0):
            distS = self.distanciaSenial()
        
        obstaculo = ((self.getObstaculoADerecha(10,0.1)!=None) or (self.getObstaculoAIzquierda(390,0.1)!=None))

        #--Condiciones
        if((frs>=self.limiteSensor)and(fls>=self.limiteSensor)and(of==None)): #No Hay Obstaculo
            if((Queque<=0)): #No Hay señal
                indice = 0
            else:   #Hay señal
                if(obstaculo):
                    if(distS>distacia): #Señal Lejana
                        indice = 1
                    else:
                        indice = 2 #Señal Cercana
                else:
                    if(distS>distacia): #Señal Lejana
                        indice = 3
                    else:
                        indice = 4 #Señal Cercana
                
        elif(((frs>self.minDistancia)or(fls>self.minDistancia))and((of==None)or(of[2]>self.minDistancia))): #Obstaculo lejos
            if((Queque<=0)): #No Hay señal
                indice = 5
            else:   #Hay señal
                if(obstaculo):
                    if(distS>distacia): #Señal Lejana
                        indice = 6
                    else:
                        indice = 7 #Señal Cercana
                else:
                    if(distS>distacia): #Señal Lejana
                        indice = 8
                    else:
                        indice = 9 #Señal Cercana
        elif(of!=None): #Obstaculo Cerca
            if((Queque<=0)): #No Hay señal
                indice = 10
            else:   #Hay señal
                if(distS>3): #Señal Lejana
                    indice = 11
                else:
                    indice = 12 #Señal Cercana

        return indice
    

    def guardarPoliticas(self):
        """
            Almacena la tabla de politicas en un archivo .txt.
        """
        np.savetxt('politicas2.txt', self.qLearning, fmt='%.5f')

    def cargarPoliticas(self):
        """
            Carga las politicas almacenadas en un archivo .txt.
        """
        try:
            self.qLearning = np.loadtxt('politicas2.txt')
        except FileNotFoundError:
            print("Error: El archivo  no existe.")
        except Exception as e:
            print(f"Se produjo un error inesperado: {e}")
    
    def visualizarPoliticas(self):
        """
            Visualiza la tabla de politicas.
        """
        filas = ['Ir a Estimulo','Evitar Obstaculo','Explorar']
        columnas = [f"S{i}" for i in range(self.cantidadEstados)]
        politicas = pd.DataFrame(self.qLearning, index=filas, columns=columnas)
        print("Q-Learning")
        print(politicas)