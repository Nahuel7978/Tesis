
from Comportamientos.BehavioralHROSbot import * 
from abc import ABC, abstractmethod
import numpy as np
import pandas as pd

class AdaptiveHROSbot(BehavioralHROSbot, ABC):
    """
        Representa al robot husuario robot con capacidades de adaptación y decisión de acción.

        Esta clase extiende de BehavioralHROSbot, heredando de la misma todos los atributos y métodos.
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

        self.cantidadAcciones = 3 #tres comportamientos(Por defecto)
        self.cantidadEstados = 13 #trece estados posibles
        
#----------

#-----Metodos Abstractos-----#
    @abstractmethod
    def ejecutar(self, accion):
        """
            Ejecuta el comportamiento pertinente en base a la acción.

            Args:
                accion(int) : [Acción tomada por el robot]
        """
        pass

    #-----
    @abstractmethod
    def estadoActual(self):
        """
            Devuelve la posicion del estado actual en la tabla de politicas.
        """

    #-----
    @abstractmethod
    def guardarPoliticas(self):
        """
            Almacena la tabla de politicas en un archivo.
        """
        pass

    #-----
    @abstractmethod
    def cargarPoliticas(self):
        """
            Carga las politicas almacenadas en un archivo.
        """
        pass
    
    
    #-----    
    @abstractmethod
    def visualizarPoliticas(self):
        """
            Visualiza la tabla de politicas.
        """
        pass

#-----Inicializacion de Atributos-----#
    def putCantidadAcciones(self, acc):
        """
            Establece la cantidad de acciones posibles en el entorno.

            Este valor define la dimensión del espacio de acciones que el agente podrá ejecutar.
            Se requiere un mínimo de dos acciones para garantizar la exploración significativa
            y la validez del algoritmo de aprendizaje por refuerzo.

            Args:
                acc (int): Número de acciones posibles.

            Raises:
                ValueError: Si el número de acciones es menor a 2.
        """
        if acc < 2:
            raise ValueError("La cantidad de acciones debe ser mayor o igual de dos.")
        self.cantidadAcciones=acc

    #----
    def getCantidadAcciones(self):
        return self.cantidadAcciones

    #-----    
    def putCantidadEstados(self, est):
        """
            Establece la cantidad de estados posibles en el entorno.

            Este valor define la dimensión del espacio de estados que el agente podrá observar.
            Se requiere un mínimo de dos estados para permitir que el agente diferencie entre situaciones
            y aprenda una política útil.

            Args:
                est (int): Número de estados posibles.

            Raises:
                ValueError: Si el número de estados es menor a 2.
        """
        if est < 2:
            raise ValueError("La cantidad de estados debe ser mayor o igual de dos.")
        self.cantidadEstados=est
    #----
    def getCantidadEstados(self):
        return self.cantidadEstados

    #-----    

    def inicializarPoliticas(self):
        """
            Inicializa la tabla de valores Q para el algoritmo Q-Learning.

            Genera una matriz de tamaño (cantidadAcciones x cantidadEstados) con valores
            aleatorios pequeños entre 0 y 0.05, lo que favorece la exploración inicial del
            espacio de políticas minimizando el sesgo hacia decisiones tempranas.

            Requiere que los atributos `self.cantidadAcciones` y `self.cantidadEstados` hayan sido
            previamente definidos mediante `putCantidadAcciones()` y `putCantidadEstados()`.

            Returns:
                None
        """
        self.qLearning = np.random.uniform(0, 0.05, size=(self.getCantidadAcciones(), self.getCantidadEstados()))

#----------

#-----Decisión de estado/acción-----        
        
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

    def vivir(self,acc):
        """
            Ejecuta los comportamientos en base a la tabla de politicas.

            Utiliza los métodos estadoActual() y en base a su retorno determina la acción llamando al método siguiente Accion(). Por último ejecuta el comportamiento pertinente.
        """
        estAct = self.estadoActual_2(acc)
        sigAcc = self.siguienteAccion(estAct)
        self.ejecutar(sigAcc)
        return sigAcc

#----------

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


#----------
    
