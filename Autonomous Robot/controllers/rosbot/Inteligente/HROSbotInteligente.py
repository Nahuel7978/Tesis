
from Comportamientos.HROSbotComportamental import * 
import numpy as np
import pandas as pd

class HROSbotInteligente(HROSbotComportamental):
    """
        Representa al robot husuario robot con capacidades de adaptación y decisión de acción.

        Esta clase extiende de HROSbotComportamental, heredando de la misma todos los atributos y métodos.
    """
    def __init__(self, bot, l_rate, t_descuento, r_exploracion):
        """
            Inicializa un objeto de tipo HROSbotInteligente.

            Llama al constructor de la clase padre e inicializa atributos que se utilizarán para la definición de comportamientos.

            Args:
                bot(bot) : [Robot]
                l_rate(float) : [Learning rate]
                t_descuento(float) : [Tasa de descuento]
                r_exploración(float) : [Ratio de exploración]
        """
        super().__init__(bot)

        self.learning_rate =l_rate
        self.tasa_descuento = t_descuento #si esta cerca de 1 busca las recompensas lejanas
        self.prob_exploracion = r_exploracion

        self.cantidadAcciones = 3 #tres comportamientos
        self.cantidadEstados = 13 #seis estados posibles

        #Inicializo la tabla de politicas con valores cercanos a ceros para agilizar la exploración, pero
        #minimizando el sesgo.
        self.qLearning = np.random.uniform(0, 0.05, size=(self.cantidadAcciones, self.cantidadEstados))
#-----

#-----Decisión de estado/acción-----        

    def estadoActual(self):
        """
            Devuelve la posicion del estado actual en la tabla de politicas.
        """
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
        
        obstaculo = ((self.getObstaculoADerecha(0.1)!=None) or (self.getObstaculoAIzquierda(0.1)!=None))

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
    
#-----

    def siguienteAccion(self, estadoActual):
        """
            A partir de un valor aleatorio se determina la siguiente accion a tomar.

            Si el valor aleatorio es menor al ratio de exploración la acción se tomará de forma al azar, en caso contrario se determinará en base al estado actual.

            Args:
                estadoActual(int) : [Estado actual en el que se encuentra el robot]
        """
        explorar = np.random.uniform()
        sigAccion = 0

        if(explorar<=self.prob_exploracion):
            print("-> Comportamiento de Exploración <-")
            sigAccion = np.random.randint(self.cantidadAcciones) 
        else:
            sigAccion = np.argmax(self.qLearning[:,estadoActual])

        return sigAccion

#-----

    def ejecutarComportamiento(self, accion):
        """
            Ejecuta el comportamiento pertinente en base a la acción.

            Args:
                accion(int) : [Acción tomada por el robot]
        """
        if(accion==0):
            self.ir_estimulo()
        elif(accion==1):
            self.evitarObstaculoGuiado()
        elif(accion==2):
            self.explorar()

#-----    
    def vivir(self):
        """
            Ejecuta los comportamientos en base a la tabla de politicas.

            Utiliza los métodos estadoActual() y en base a su retorno determina la acción llamando al método siguiente Accion(). Por último ejecuta el comportamiento pertinente.
        """
        estAct = self.estadoActual()
        sigAcc = self.siguienteAccion(estAct)
        self.ejecutarComportamiento(sigAcc)
#-----

#----Políticas------     
    def actualizarPoliticas(self, estadoActual, accionTomada, estadoSiguiente, accionSiguiente, recompensa):
        """
            Actualiza las politicas a través de Q-Learning por medio del método de Sarsa.

            Args:
                estadoActual(int) : [Estado actual en el que se encuentra el robot]
                accionTomada(int) : [Acción tomada por el robot]
                estadoSiguiente(int) : [Estado siguiente del robot en base a la accion tomada]
                accionSiguiente(int) : [Acción elegida a tomar luego de la acción tomada]
                recompensa(int) : [Recompensa recibida por la acción tomada]

        """
        #Q(s,a)
        qActual = self.qLearning[accionTomada][estadoActual]
        print("qActual: qLearning[",accionTomada,"][",estadoActual,"]= ",qActual)

        #Q(s',a')
        qSiguiente = self.qLearning[accionSiguiente][estadoSiguiente]

        print("qSiguiente: qLearning[",accionSiguiente,"][",estadoSiguiente,"]= ",qSiguiente)

        ## Q(s,a) = Q(s,a)+ lr*(r + td*Q(s',a')-Q(s,a))
        self.qLearning[accionTomada][estadoActual] = qActual + (self.learning_rate*(recompensa+(self.tasa_descuento*qSiguiente)-qActual))

        print("qActual Mej: qLearning[",accionTomada,"][",estadoActual,"]= ",self.qLearning[accionTomada][estadoActual])

#-----    
    
    def visualizarPoliticas(self):
        """
            Visualiza la tabla de politicas.
        """
        filas = ['Ir a Estimulo','Evitar Obstaculo','Explorar']
        columnas = [f"S{i}" for i in range(self.cantidadEstados)]
        politicas = pd.DataFrame(self.qLearning, index=filas, columns=columnas)
        print("Q-Learning")
        print(politicas)

#-----

    def guardarPoliticas(self):
        """
            Almacena la tabla de politicas en un archivo .txt.
        """
        np.savetxt('politicas.txt', self.qLearning, fmt='%.5f')

#-----

    def cargarPoliticas(self):
        """
            Carga las politicas almacenadas en un archivo .txt.
        """
        try:
            self.qLearning = np.loadtxt('politicas.txt')
        except FileNotFoundError:
            print("Error: El archivo  no existe.")
        except Exception as e:
            print(f"Se produjo un error inesperado: {e}")

#--------
    
