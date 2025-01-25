
from abc import ABC, abstractmethod
from Qlearning.AdaptiveHROSbot import *

class BehavioralAdaptativeHROSbot(AdaptiveHROSbot):

    def __init__(self, bot, l_rate, t_descuento, r_exploracion):
        super().__init__(bot, l_rate, t_descuento, r_exploracion)
        self.putCantidadAcciones(3)
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
        if(accion==0):
            self.ir_estimulo()
        elif(accion==1):
            self.evitarObstaculo()
        elif(accion==2):
            self.explorar()
        else:
            raise ValueError(f"Acción no válida: {accion}")

    def guardarPoliticas(self):
        """
            Almacena la tabla de politicas en un archivo .txt.
        """
        np.savetxt('politicas.txt', self.qLearning, fmt='%.5f')

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