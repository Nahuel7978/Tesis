from abc import ABC, abstractmethod
from Qlearning.AdaptiveHROSbot import *

class ActionAdaptativeHROSbot(AdaptiveHROSbot):

    def __init__(self, bot, l_rate, t_descuento, r_exploracion):
        super().__init__(bot, l_rate, t_descuento, r_exploracion)
        self.putCantidadAcciones(14)
        self.inicializarPoliticas()

    def ejecutar(self, accion):
        if(accion == 0):
            print("---> avanzarSenial")
            self.avanzarSenial()
        elif(accion == 1):
            print("---> giroSenial")
            self.giroSenial()
        elif(accion == 2):
            print("---> avanzarUltimaSenial")
            self.avanzarUltimaSenial()
        elif(accion == 3):
            print("---> avanzarParaleloObstaculo")
            self.avanzarParaleloObstaculo()
        elif(accion == 4):
            print("---> giroParaleloObstaculoGuiado")
            self.giroParaleloObstaculoGuiado()
        elif(accion == 5):
            print("---> giroParaleloObstaculo")
            self.giroParaleloObstaculo()
        elif(accion == 6):
            print("---> giroIzquierdaParaleloObstaculo")
            self.giroIzquierdaParaleloObstaculo()
        elif(accion == 7):
            print("---> giroDerechaParaleloObstaculo")
            self.giroDerechaParaleloObstaculo()
        elif(accion == 8):
            print("---> avanzarObstaculo")
            self.avanzarObstaculo()
        elif(accion == 9):
            print("---> giroAleatorioIzquierda")
            self.giroAleatorioIzquierda()
        elif(accion == 10):
            print("---> Giro Aleatorio Derecha")
            self.giroAleatorioDerecha()
        elif(accion == 11):
            print("---> Avanzar Mucho")
            self.avanzar(self.distAvanceMax, self.speed) ##Avanzar mucho
        elif(accion == 12):
            print("---> Avanzar Medio")
            self.avanzar(self.distAvanceMedio, self.speed) ##Avanzar medio
        elif(accion == 13):
            print("---> Avanzar Poco")
            self.avanzar(self.distAvanceMin, self.speed) ##Avanzar
        else:
            print("----> Retroceder Poco")
            self.retroceder(self.distAvanceMin, self.speed) ##Retroceder
        """elif(accion == 15):
            self.retroceder(self.distAvanceMax, self.speed) ##Retroceder mucho
        elif(accion == 16):
            self.retroceder(self.distAvanceMedio, self.speed) ##Retroceder poco"""
        

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

    def visualizarPoliticas(self):
        """
            Visualiza la tabla de politicas.
        """
        filas = ['Avanzar Senial','Giro Senial','Avanzar Ultima Senial', 'Avanzar Paralelo Obstaculo', 'Giro Paralelo Obstaculo Guiado', 'Giro Paralelo Obstaculo',
                 'Giro Izquierda Paralelo Obstaculo', 'Giro Derecha Paralelo Obstaculo','Avanzar Obstaculo', 'Giro Aleatorio Izquierda', 
                 'Giro Aleatorio Derecha', 'Avanzar Mucho', 'Avanzar Medio', 'Avanzar Poco']
        columnas = [f"S{i}" for i in range(self.cantidadEstados)]
        politicas = pd.DataFrame(self.qLearning, index=filas, columns=columnas)
        print("Q-Learning")
        print(politicas)