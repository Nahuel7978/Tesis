from abc import ABC, abstractmethod
from Qlearning.AdaptiveHROSbot import *

class ActionAdaptativeHROSbot(AdaptiveHROSbot):

    def __init__(self, bot, l_rate, t_descuento, r_exploracion):
        super().__init__(bot, l_rate, t_descuento, r_exploracion)
        self.putCantidadAcciones(15)
        self.putCantidadEstados((58*15)) 
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
            print("---> giroIzquierdaParaleloObstaculo")
            ejecucion = self.giroIzquierdaParaleloObstaculo()
        elif(accion == 7):
            print("---> giroDerechaParaleloObstaculo")
            ejecucion = self.giroDerechaParaleloObstaculo()
        elif(accion == 8):
            print("---> avanzarObstaculo")
            ejecucion = self.avanzarObstaculo()
        elif(accion == 9):
            print("---> giroAleatorioIzquierda")
            ejecucion = self.giroAleatorioIzquierda()
        elif(accion == 10):
            print("---> Giro Aleatorio Derecha")
            ejecucion = self.giroAleatorioDerecha()
        elif(accion == 11):
            print("---> Avanzar Mucho")
            distanciaActual = self.distanciaRecorrida
            ejecucion = self.avanzar(self.distAvanceMax, self.speed) ##Avanzar mucho

            if((not ejecucion)and(self.distanciaRecorrida>(distanciaActual+self.distAvanceMedio))):
                ejecucion = True
            else:
                print(self.distanciaRecorrida,"> (", distanciaActual,"+",self.distAvanceMedio,")")

        elif(accion == 12):
            print("---> Avanzar Medio")
            distanciaActual = self.distanciaRecorrida
            ejecucion = self.avanzar(self.distAvanceMedio, self.speed) ##Avanzar medio

            if((not ejecucion)and(self.distanciaRecorrida>(distanciaActual+self.distAvanceMin))):
                ejecucion = True
            else:
                print(self.distanciaRecorrida,"> (", distanciaActual,"+",self.distAvanceMin,")")

        elif(accion == 13):
            print("---> Avanzar Poco")
            ejecucion = self.avanzar(self.distAvanceMin, self.speed) ##Avanzar
        elif(accion == 14):
            print("----> Retroceder Poco")
            ejecucion = self.retroceder(0.4, self.speed) ##Retroceder
        else:
            raise ValueError(f"Acción no válida: {accion}")

        return ejecucion
        
    def estadoActual(self, accion):
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
            orient = self.orientacionUltimaSenial()
        
        od, minD = self.getObstaculoADerecha(30)
        #print("Indice a derecha: ", od, " - Dist Der: ", minD)
        oi, minI = self.getObstaculoAIzquierda(370)
        #print("Indice a izq: ", oi, " - Dist Izq: ", minI)
        obstaculoDer = (od!=None)
        obstaculoIzq = (oi!=None)

        #--Condiciones
        if((frs>=self.limiteSensor)and(fls>=self.limiteSensor)and(of==None)): #No Hay Obstaculo en frente
            if((Queque<=0)): #No Hay señal
                if(obstaculoIzq and obstaculoDer):
                    indice = 0

                elif(obstaculoIzq):
                    indice = 1
                
                elif(obstaculoDer):
                    indice = 2
                
                else: 
                    indice = 3

            else:   #Hay señal
                if(obstaculoIzq and obstaculoDer): #Obstaculo en ambos lados
                    if(distS>distacia): #Señal Lejana
                        if(orient==1):
                            indice = 4 # Señal a izquierda
                        else:
                            indice = 5 # Señal a derecha
                    else:
                        if(orient==1):
                            indice = 6 # Señal a izquierda
                        else:
                            indice = 7 # Señal a derecha
                
                elif(obstaculoIzq): ##Obstaculo a la izquiera
                    if(distS>distacia): #Señal Lejana
                        if(orient==1):
                            indice = 8
                        else:
                            indice = 9
                    else:
                        if(orient==1):
                            indice = 10 #Señal Cercana
                        else:
                            indice = 11

                elif(obstaculoDer): ##Obstaculo a la derecha
                    if(distS>distacia): #Señal Lejana
                        if(orient==1):
                            indice = 12
                        else:
                            indice = 13
                    else:
                        if(orient==1):
                            indice = 14
                        else:
                            indice = 15

                else: ## Sin obstaculos
                    if(distS>distacia): #Señal Lejana
                        if(orient==1):
                            indice = 16
                        else:
                            indice = 17
                    else:
                        if(orient==1):
                            indice = 18
                        else:
                            indice = 19
                
        elif(((frs>self.minDistancia)or(fls>self.minDistancia))and((of==None)or(of[2]>self.minDistancia))): #Obstaculo en frente lejos
            if((Queque<=0)): #No Hay señal
                if(obstaculoIzq and obstaculoDer):
                    indice = 20

                elif(obstaculoIzq):
                    indice = 21
                
                elif(obstaculoDer):
                    indice = 22
                
                else: 
                    indice = 23
            else:   #Hay señal
                if(obstaculoIzq and obstaculoDer): #Obstaculo en ambos lados
                    if(distS>distacia): #Señal Lejana
                        if(orient==1):
                            indice = 24
                        else:
                            indice = 25
                    else:
                        if(orient==1):
                            indice = 26
                        else:
                            indice = 27
                
                elif(obstaculoIzq): ##Obstaculo a la izquiera
                    if(distS>distacia): #Señal Lejana
                        if(orient==1):
                            indice = 28
                        else:
                            indice = 29
                    else:
                        if(orient==1):
                            indice = 30
                        else:
                            indice = 31

                elif(obstaculoDer): ##Obstaculo a la derecha
                    if(distS>distacia): #Señal Lejana
                        if(orient==1):
                            indice = 32
                        else:
                            indice = 33
                    else:
                        if(orient==1):
                            indice = 34
                        else:
                            indice = 35
                else: ## Sin obstaculos a los lados
                    if(distS>distacia): #Señal Lejana
                        if(orient==1):
                            indice = 36
                        else:
                            indice = 37
                    else:
                        if(orient==1):
                            indice = 38
                        else:
                            indice = 39

        elif(of!=None): #Obstaculo en frente Cerca
            if((Queque<=0)): #No Hay señal
                if(obstaculoIzq and obstaculoDer):
                    indice = 40

                elif(obstaculoIzq):
                    indice = 41
                
                elif(obstaculoDer):
                    indice = 42
                
                else: 
                    indice = 43
            else:   #Hay señal
                if(obstaculoIzq and obstaculoDer): #Obstaculo en ambos lados
                    indice = 44 ## Solo importa salir
                
                elif(obstaculoIzq): ##Obstaculo a la izquiera
                    if(distS>distacia): #Señal Lejana
                        if(orient==1):
                            indice = 45
                        else:
                            indice = 46
                    else:
                        if(orient==1):
                            indice = 47
                        else:
                            indice = 48

                elif(obstaculoDer): ##Obstaculo a la derecha
                    if(distS>distacia): #Señal Lejana
                        if(orient==1):
                            indice = 49
                        else:
                            indice = 50
                    else:
                        if(orient==1):
                            indice = 51 #Señal Cercana
                        else:
                            indice = 52
                else: ## Sin obstaculos
                    if(distS>distacia): #Señal Lejana
                        if(orient==1):
                            indice = 53
                        else:
                            indice = 54
                    else:
                        if(orient==1):
                            indice = 55
                        else:
                            indice = 56

        if(accion == 0):
            return indice
        else:
            return indice+(58*(accion-1))

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
                 'Giro Aleatorio Derecha', 'Avanzar Mucho', 'Avanzar Medio', 'Avanzar Poco','Retroceder']
        columnas = [f"S{i}" for i in range(self.cantidadEstados)]
        politicas = pd.DataFrame(self.qLearning, index=filas, columns=columnas)
        print("Q-Learning")
        print(politicas)