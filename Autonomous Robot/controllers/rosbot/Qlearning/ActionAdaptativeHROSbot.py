from abc import ABC, abstractmethod
from Qlearning.AdaptiveHROSbot import *

class ActionAdaptativeHROSbot(AdaptiveHROSbot):

    def __init__(self, bot, l_rate, t_descuento, r_exploracion):
        super().__init__(bot, l_rate, t_descuento, r_exploracion)
        self.putCantidadAcciones(13)
        self.candidaAmbientes = 32
        self.putCantidadEstados((self.candidaAmbientes*self.getCantidadAcciones())) 
        self.ambienteActual = 0
        self.inicializarPoliticas()
        

    def ejecutar(self, accion):
        ejecucion = False
        if(accion == 0):
            print("---> avanzarSenial")
            ejecucion = self.avanzarSenial()
        elif(accion == 1):
            print("---> giroSenial")
            ejecucion = self.giroSenial()
        elif(accion == 2):
            print("---> avanzarUltimaSenial")
            ejecucion = self.avanzarUltimaSenial()
        elif(accion == 3):
            print("---> avanzarParaleloObstaculo")
            ejecucion = self.avanzarParaleloObstaculo()
        elif(accion == 4):
            print("---> giroParaleloObstaculoGuiado")
            ejecucion = self.giroParaleloObstaculoGuiado()
        elif(accion == 5):
            print("---> giroParaleloObstaculo")
            ejecucion = self.giroParaleloObstaculo()

        elif(accion == 6):
            print("---> avanzarObstaculo")
            ejecucion = self.avanzarObstaculo()
        elif(accion == 7):
            print("---> giroAleatorioIzquierda")
            ejecucion = self.giroAleatorioIzquierda()
        elif(accion == 8):
            print("---> Giro Aleatorio Derecha")
            ejecucion = self.giroAleatorioDerecha()
        elif(accion == 9):
            print("---> Avanzar Mucho")
            distanciaActual = self.distanciaRecorrida
            ejecucion = self.avanzar(self.distAvanceMax, self.speed) ##Avanzar mucho

            if((not ejecucion)and(self.distanciaRecorrida>(distanciaActual+self.distAvanceMedio))):
                ejecucion = True
            else:
                print(self.distanciaRecorrida,"> (", distanciaActual,"+",self.distAvanceMedio,")")

        elif(accion == 10):
            print("---> Avanzar Medio")
            distanciaActual = self.distanciaRecorrida
            ejecucion = self.avanzar(self.distAvanceMedio, self.speed) ##Avanzar medio

            if((not ejecucion)and(self.distanciaRecorrida>(distanciaActual+self.distAvanceMin))):
                ejecucion = True
            else:
                print(self.distanciaRecorrida,"> (", distanciaActual,"+",self.distAvanceMin,")")

        elif(accion == 11):
            print("---> Avanzar Poco")
            ejecucion = self.avanzar(self.distAvanceMin, self.speed) ##Avanzar
        elif(accion == 12):
            print("----> Retroceder Poco")
            ejecucion = self.retroceder(0.4, self.speed) ##Retroceder
        else:
            raise ValueError(f"Acción no válida: {accion}")

        return ejecucion
        

    def estadoActual(self,accion):
        """_summary_

        Args:
            accion (_type_): _description_

        Returns:
            _type_: _description_
        """
        amb = self.deteccionAmbiente()
        return amb+(self.candidaAmbientes*(accion-1))

    def deteccionAmbiente(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        indice = 0
        dif_sensores = 0.02
        min_dif = 0.06
        dist_min = 0.15
        self.robot.step(self.robotTimestep)
        #--Parámetros
        ob_f = self.getObstaculoAlFrente()
        fls =self.frontLeftSensor.getValue() 
        frs = self.frontRightSensor.getValue()

        od, minD = self.getObstaculoADerecha(30)
        oi, minI = self.getObstaculoAIzquierda(370)
        print("Indice a der: ", od, " - Dist Der: ", minD, " - fls: ",fls,">=",frs+dif_sensores," :frs")
        print("Indice a izq: ", oi, " - Dist Izq: ", minI, " - fls: ",fls+dif_sensores,"<=",frs," :frs")
        print(" ")
        obstaculoDer =(((od!=None)and(minD<minI)) 
                        or ((od==None)and(frs+dif_sensores)<=fls))

        obstaculoIzq = (((oi!=None)and(minI<minD)) 
                        or ((oi==None) and((fls+dif_sensores)<=frs)))

        obstaculoCercano = ((ob_f != None)or((frs<self.minDistancia)or(fls<self.minDistancia)))
        obstaculoLejano = ((ob_f==None)and((frs<self.limiteSensor)or(fls<self.limiteSensor)))

        esquina = self.getEsquinaFrontal()

        print("cercano:",obstaculoCercano)
        print("lejano:",obstaculoLejano)
        print("izq:",obstaculoIzq)
        print("der:", obstaculoDer)
        print("Esquina", esquina)
        dist_senial = self.get_distanciaUltimaSenial()
        

        if(dist_senial == None):
            if(obstaculoCercano): ## Obstaculo cercano
                if(esquina or (obstaculoDer and obstaculoIzq)):
                    indice = 0
                elif(obstaculoDer): 
                    indice = 1
                elif(obstaculoIzq):
                    indice = 2
                else: ## Solo un obstaculo en frente
                    indice = 3

            elif(obstaculoLejano): ## Obstaculo lejano
                if(esquina or (obstaculoDer and obstaculoIzq)):
                    indice = 4
                elif(obstaculoDer): 
                    indice = 5
                elif(obstaculoIzq):
                    indice = 6
                else: ## Solo un obstaculo en frente
                    indice = 7
            else:
                if(esquina or (obstaculoDer and obstaculoIzq)):
                    indice = 8
                elif(obstaculoDer): 
                    indice = 9
                elif(obstaculoIzq):
                    indice = 10
                else: ## Vía libre
                    indice = 11

        else: ## Hay señal almacenada
            orientacion_señal = self.orientacionUltimaSenial()
            if (obstaculoCercano): ## Obstaculo cercano
                    if(esquina or (obstaculoDer and obstaculoIzq)):
                        indice = 12
                    elif(obstaculoDer): 
                        indice = 13
                    elif(obstaculoIzq):
                        indice = 14
                    else: ## Solo un obstaculo en frente
                        indice = 15

            elif(orientacion_señal == 1 ):
                if(obstaculoLejano): ## Obstaculo lejano
                    if(esquina or (obstaculoDer and obstaculoIzq)):
                        indice = 16
                    elif(obstaculoDer): 
                        indice = 17
                    elif(obstaculoIzq):
                        indice = 18
                    else: ## Solo un obstaculo en frente
                        indice = 19
                else:
                    if(esquina or (obstaculoDer and obstaculoIzq)):
                        indice = 20
                    elif(obstaculoDer): 
                        indice = 21
                    elif(obstaculoIzq):
                        indice = 22
                    else: ## Vía libre
                        indice = 23            
            else:
                if(obstaculoLejano): ## Obstaculo lejano
                    if(esquina  or (obstaculoDer and obstaculoIzq)):
                        indice = 24
                    elif(obstaculoDer): 
                        indice = 25
                    elif(obstaculoIzq):
                        indice = 26
                    else: ## Solo un obstaculo en frente
                        indice = 27
                else:
                    if(esquina  or (obstaculoDer and obstaculoIzq)):
                        indice = 28
                    elif(obstaculoDer): 
                        indice = 29
                    elif(obstaculoIzq):
                        indice = 30
                    else: ## Vía Libre
                        indice = 31

        print("Ambiente Actual:", indice)
        
        self.ambienteActual = indice

        return indice


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
                 'Avanzar Obstaculo', 'Giro Aleatorio Izquierda', 
                 'Giro Aleatorio Derecha', 'Avanzar Mucho', 'Avanzar Medio', 'Avanzar Poco','Retroceder']
        columnas = [f"S{i}" for i in range(self.cantidadEstados)]
        politicas = pd.DataFrame(self.qLearning, index=filas, columns=columnas)
        print("Q-Learning")
        print(politicas)

    def get_ambienteActual(self):
        return self.ambienteActual