from abc import ABC, abstractmethod
from Qlearning.AdaptiveHROSbot import *

class ActionAdaptativeHROSbot(AdaptiveHROSbot):

    def __init__(self, bot, l_rate, t_descuento, r_exploracion):
        super().__init__(bot, l_rate, t_descuento, r_exploracion)
        self.putCantidadAcciones(17)
        self.inicializarPoliticas()

    def ejecutar(self, accion):
        if(accion == 0):
            self.avanzarSenial()
        elif(accion == 1):
            self.giroSenial()
        elif(accion == 2):
            self.avanzarUltimaSenial()
        elif(accion == 3):
            self.avanzarParaleloObstaculo()
        elif(accion == 4):
            self.giroParaleloObstaculoGuiado()
        elif(accion == 5):
            self.giroParaleloObstaculo()
        elif(accion == 6):
            self.giroIzquierdaParaleloObstaculo()
        elif(accion == 7):
            self.giroDerechaParaleloObstaculo()
        elif(accion == 8):
            self.avanzarObstaculo()
        elif(accion == 9):
            self.retrocederObstaculo()
        elif(accion == 10):
            self.giroAleatorioIzquierda()
        elif(accion == 11):
            self.giroAleatorioDerecha()
        elif(accion == 12):
            self.avanzar(4, self.speed) ##Avanzar mucho
        elif(accion == 13):
            self.avanzar(2, self.speed) ##Avanzar medio
        elif(accion == 14):
            self.avanzar(1, self.speed) ##Avanzar
        elif(accion == 15):
            self.retroceder(4, self.speed) ##Retroceder mucho
        elif(accion == 16):
            self.retroceder(2, self.speed) ##Retroceder poco
        else:
            self.retroceder(1, self.speed) ##Retroceder

    def guardarPoliticas(self):
        """
            Almacena la tabla de politicas en un archivo .txt.
        """
        np.savetxt('politicas_adaptativas.txt', self.qLearning, fmt='%.5f')

    def cargarPoliticas(self):
        """
            Carga las politicas almacenadas en un archivo .txt.
        """
        try:
            self.qLearning = np.loadtxt('politicas_adaptativas.txt')
        except FileNotFoundError:
            print("Error: El archivo  no existe.")
        except Exception as e:
            print(f"Se produjo un error inesperado: {e}")