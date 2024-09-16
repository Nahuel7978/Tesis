
from Comportamientos.HROSbotComportamental import * 
import numpy as np
import pandas as pd

class HROSbotInteligente(HROSbotComportamental):
    def __init__(self, bot, l_rate, t_descuento, r_exploracion):
        super().__init__(bot)

        self.learning_rate =l_rate
        self.tasa_descuento = t_descuento #si esta cerca de 1 busca las recompensas lejanas
        self.prob_exploracion = r_exploracion

        self.cantidadAcciones = 3 #tres comportamientos
        self.cantidadEstados = 13 #seis estados posibles

        #Inicializo la tabla de politicas con valores cercanos a ceros para agilizar la exploración, pero
        #minimizando el sesgo.
        self.qLearning = np.random.uniform(0, 0.05, size=(self.cantidadAcciones, self.cantidadEstados))
        

    #-Devuelve la posicion del estado actual en la tabla de politicas.
    def estadoActual(self):
        indice = 0
        distacia = 3
        self.robot.step(self.robotTimestep)
        #--Parámetros
        of = self.getObstaculoAlFrente()
        fls =self.frontLeftSensor.getValue() 
        frs = self.frontRightSensor.getValue()
        Queque = self.receiver.getQueueLength()
        if(Queque>0):
            distS = self.distanciaSeñal()
        
        obstaculo = ((self.getObstaculoADerecha(0.1)!=None) or (self.getObstaculoAIzquierda(0.1)!=None))
        #
        #--Condiciones
        if((frs>=self.limiteSensor)and(fls>=self.limiteSensor)): #No Hay Obstaculo
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
                
        elif(((frs>self.minDistancia)or(fls>self.minDistancia))and(of==None)): #Obstaculo lejos
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
    
    #--Determina la siguiente accion a tomar.
    def siguienteAccion(self, estadoActual):
        explorar = np.random.uniform()
        sigAccion = 0

        #Determino si la siguiente acción es explorar.
        if(explorar<=self.prob_exploracion):
            print("-> Comportamiento de Exploración <-")
            sigAccion = np.random.randint(self.cantidadAcciones) 
        else:
            sigAccion = np.argmax(self.qLearning[:,estadoActual])

        return sigAccion

    #--Actualizacion por el método de Sarsa. 
    def actualizarPoliticas(self, estadoActual, accionTomada, estadoSiguiente, accionSiguiente, recompensa):
        #Q(s,a)
        qActual = self.qLearning[accionTomada][estadoActual]
        print("qActual: qLearning[",accionTomada,"][",estadoActual,"]= ",qActual)

        #Q(s',a')
        qSiguiente = self.qLearning[accionSiguiente][estadoSiguiente]

        print("qSiguiente: qLearning[",accionSiguiente,"][",estadoSiguiente,"]= ",qSiguiente)

        ## Q(s,a) = Q(s,a)+ lr*(r + td*Q(s',a')-Q(s,a))
        self.qLearning[accionTomada][estadoActual] = qActual + (self.learning_rate*(recompensa+(self.tasa_descuento*qSiguiente)-qActual))

        print("qActual Mej: qLearning[",accionTomada,"][",estadoActual,"]= ",self.qLearning[accionTomada][estadoActual])

    #--Ejecuta el comportamiento pertinente
    def ejecutarComportamiento(self, accion):
        if(accion==0):
            self.ir_estimulo()
        elif(accion==1):
            self.evitarObstaculoGuiado()
        elif(accion==2):
            self.explorar()

    #--Ejecuta los comportamientos en base a lo aprendido
    def vivir(self):
        estAct = self.estadoActual()
        sigAcc = self.siguienteAccion(estAct)
        self.ejecutarComportamiento(sigAcc)

    def visualizarPoliticas(self):
        filas = ['Ir a Estimulo','Evitar Obstaculo','Explorar']
        columnas = [f"S{i}" for i in range(self.cantidadEstados)]
        politicas = pd.DataFrame(self.qLearning, index=filas, columns=columnas)
        print("Q-Learning")
        print(politicas)

    def guardarPoliticas(self):
        np.savetxt('politicas.txt', self.qLearning, fmt='%.5f')

    def cargarPoliticas(self):
        try:
            self.qLearning = np.loadtxt('politicas.txt')
        except FileNotFoundError:
            print("Error: El archivo  no existe.")
        except Exception as e:
            print(f"Se produjo un error inesperado: {e}")

    
