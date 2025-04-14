import math
from controller import Robot, Camera, Motor, Receiver
from Navegacion.MapaNavegacion import *
import numpy as np
from itertools import combinations
from sklearn.linear_model import RANSACRegressor
import warnings
from sklearn.exceptions import UndefinedMetricWarning

class HROSbot: 
    """
    Representa al robot Husuarion Rosbot.
    """
    def __init__(self, bot):
        """
           Inicializa un objeto de tipo HROSbot.

            Habilita los dispositivos del robot.

            Args:
                robot (bot): [Robot]
        """

        #---Inicialización.
        self.robot = bot
        self.robotTimestep = int(self.robot.getBasicTimeStep())
        self.TIMESTEP = 64

        #---Atributos.
        self.speedMax = 8
        self.speed = 5
        self.speedMin = 2

        self.distAvanceMax = 3
        self.distAvanceMedio = 2
        self.distAvanceMin = 1

        self.pasos = 200

        #---Activación de moteres.
        self.ruedaDerechaSuperior = self.robot.getDevice("fr_wheel_joint")
        self.ruedaDerechaInferior = self.robot.getDevice("rr_wheel_joint")
        self.ruedaIzquierdaSuperior = self.robot.getDevice("fl_wheel_joint")
        self.ruedaIzquierdaInferior = self.robot.getDevice("rl_wheel_joint")

        self.ruedaDerechaSuperior.setPosition(float('inf'))
        self.ruedaDerechaInferior.setPosition(float('inf'))
        self.ruedaIzquierdaInferior.setPosition(float('inf'))
        self.ruedaIzquierdaSuperior.setPosition(float('inf'))

        #---Activación de giroscopio.
        self.giroscopio = self.robot.getDevice("imu gyro")
        self.giroscopio.enable(self.robotTimestep)

        #---Activación de acelerometro.
        self.acelerometro = self.robot.getDevice("imu accelerometer")
        self.acelerometro.enable(self.robotTimestep)

        #---Activación del lidar-
        self.lidar = self.robot.getDevice("laser")
        self.lidar.enable(self.robotTimestep)
        self.lidar.enablePointCloud()

        self.front_range = 20
        self.back_range = 20
        self.error_range = 3

        #---Activación de Sensores infrarojos.
        self.frontLeftSensor = self.robot.getDevice("fl_range")
        self.frontRightSensor = self.robot.getDevice("fr_range")
        self.rearLeftSensor = self.robot.getDevice("rl_range")
        self.rearRightSensor = self.robot.getDevice("rr_range")
        
        self.frontLeftSensor.enable(self.robotTimestep)
        self.frontRightSensor.enable(self.robotTimestep)
        self.rearLeftSensor.enable(self.robotTimestep)
        self.rearRightSensor.enable(self.robotTimestep)

        self.limiteSensor = 2.0
        self.minDistancia = 0.3

        #---Activación de sensores de posición.
        self.frontLeftPositionSensor = self.robot.getDevice("front left wheel motor sensor")
        self.frontRightPositionSensor = self.robot.getDevice("front right wheel motor sensor")
        self.rearLeftPositionSensor = self.robot.getDevice("rear left wheel motor sensor")
        self.rearRightPositionSensor = self.robot.getDevice("rear right wheel motor sensor")
        
        self.frontLeftPositionSensor.enable(self.TIMESTEP)
        self.frontRightPositionSensor.enable(self.TIMESTEP)
        self.rearLeftPositionSensor.enable(self.TIMESTEP)
        self.rearRightPositionSensor.enable(self.TIMESTEP)

        self.anteriorValorPositionSensor = [0,0,0,0]
        self.DefaultPositionSensorAnterior()

        self.distanciaRecorrida = 0

        #---Activación Receiver
        self.receiver = self.robot.getDevice('Receiver')
        self.receiver.enable(32)

        self.direccionUltimaSenial = None
        self.distanciaUltimaSenial = None

        #---Atributos propios de las ruedas.
        self.radioRueda = 0.0425
        self.encoderUnit = (2*np.pi*self.radioRueda)/6.28 
        
        #---Objeto mapa
        self.mapping = MapaNavegacion(self)

        self.detener()
 
 #-----Acciones primarias-----
    def avanzar(self, distancia, velocidad):
        """ 
            Permite avanzar al robot. 

            Activa los motores de las ruedas a una determinada velocidad y los desactiva luego de una determinada distancia.
            Avanza siempre y cuando no detecte un obstaculo en frente con el lidar.

            Args:
                distancia (float): [Distancia]
                velociada (float): [Velocidad]

            Retorna True si el robot pudo avanzar y False en caso contrario.
        """
        print("  ⬆ Avanzar")
        dist = [0, 0]
        dist[0] = 0
        dist[1] = 0

        self.robot.step(self.robotTimestep)
        fls = self.frontLeftSensor.getValue()
        frs = self.frontRightSensor.getValue()

        if(fls>self.minDistancia and frs>self.minDistancia):
            dist_ant=self.metrosRecorridos()
            p = 0

            while ((self.getObstaculoAlFrente()==None)and
                (dist[0]<distancia or dist[1]<distancia)and
                (self.robot.step(self.robotTimestep) != -1)):
                dist =  self.metrosRecorridos()
                self.ruedaDerechaSuperior.setVelocity(velocidad)
                self.ruedaDerechaInferior.setVelocity(velocidad)
                self.ruedaIzquierdaInferior.setVelocity(velocidad)
                self.ruedaIzquierdaSuperior.setVelocity(velocidad)
                if(dist==dist_ant):
                    p+=1
                if(p == self.pasos):
                    break;
                
                dist_ant = dist

        self.detener()

        self.anteriorValorPositionSensor[0] = self.frontLeftPositionSensor.getValue()
        self.anteriorValorPositionSensor[1] = self.frontRightPositionSensor.getValue()


        self.mapping.update({'type': 'avance', 'value': max(dist)})

        if((dist[0]>=distancia) or (dist[1]>=distancia)):
            return True
        else:
            return False

    def retroceder(self, distancia, velocidad):
        """ 
            Permite retroceder al robot. 

            Activa los motores de las ruedas a una determinada velocidad y los desactiva luego de una determinada distancia.

            Args:
                distancia (float): [Distancia determinada]
                velociada (float): [Velocidad determinada]
            
            Retorna True si el robot pudo retoroceder y False en caso contrario.
        """

        print("  ⬇ Retroceder")
        dist = [0, 0]
        distancia = -1*distancia
        self.robot.step(self.robotTimestep)
        self.anteriorValorPositionSensor[2] = self.rearLeftPositionSensor.getValue()
        self.anteriorValorPositionSensor[3] = self.rearRightPositionSensor.getValue()


        rls = self.rearLeftSensor.getValue()
        rrs = self.rearRightSensor.getValue()

        dist[0] = 0
        dist[1] = 0
        
        if(rls>(self.minDistancia-0.1) and rrs>(self.minDistancia-0.1)):
            pasos= 0
            dist_ant = self.metrosRecorridosHaciaAtras()
            while ((self.getObstaculoAtras()==None)and
                (dist[0]>distancia or dist[1]>distancia)and
                (self.robot.step(self.robotTimestep) != -1)):
                    
                #dist =  self.metrosRecorridos()
                dist = self.metrosRecorridosHaciaAtras()
                self.ruedaDerechaSuperior.setVelocity(-velocidad)
                self.ruedaDerechaInferior.setVelocity(-velocidad)
                self.ruedaIzquierdaInferior.setVelocity(-velocidad)
                self.ruedaIzquierdaSuperior.setVelocity(-velocidad)
                if(dist==dist_ant):
                    pasos+=1

                if(pasos == self.pasos):
                    break;
                
                dist_ant = dist

                
        self.detener()
        
        self.anteriorValorPositionSensor[2] = self.rearLeftPositionSensor.getValue()
        self.anteriorValorPositionSensor[3] = self.rearRightPositionSensor.getValue()

        if((dist[0]<=distancia) or (dist[1]<=distancia)):
            return True
        else:
            return False
    

    def giroDerecha(self, angulo):
        """ 
            Permite girar hacia la derecha al robot. 

            Activa los motores izquierdos de las ruedas a una velocidad predefinida y los desactiva luego de una determinado angulo de giro.

            Args:
                angulo (float): [Angulo de giro]
            
            Retorna True si el robot pudo hacer el giro y False en caso contrario.
        """
        print("  ⮕ Derecha")
        velocidad = 2.0
        ang_z = 0
        giro = False

        self.robot.step(self.robotTimestep)
        obstaculo, min= self.getObstaculoADerecha(40)
        frs = self.frontRightSensor.getValue()
        print("frs=",frs)
        #print("obst_d=",obstaculo[0])
        if(obstaculo==None and frs>=self.minDistancia-0.12):
            giro = True
            gyroZ =self.giroscopio.getValues()[2]
            ang_z_ant=ang_z+(gyroZ*self.robotTimestep*0.001)
            pasos=0

            while ((self.robot.step(self.robotTimestep) != -1)and
                   (ang_z>(angulo))):
                gyroZ =self.giroscopio.getValues()[2]
                ang_z=ang_z+(gyroZ*self.robotTimestep*0.001)
            
                self.ruedaDerechaSuperior.setVelocity(0.0)
                self.ruedaDerechaInferior.setVelocity(0.0)
                self.ruedaIzquierdaInferior.setVelocity(velocidad)
                self.ruedaIzquierdaSuperior.setVelocity(velocidad)
                
                if(ang_z==ang_z_ant):
                    paso+=1
                if(pasos == self.pasos):
                    giro=False
                    break;
                ang_z_ant = ang_z
                
        self.detener()

        self.mapping.update({'type': 'giro', 'value': ang_z})

        return giro

    def giroIzquierda(self, angulo):
        """ 
            Permite girar hacia la derecha al robot. 

            Activa los motores derechos de las ruedas a una velocidad predefinida y los desactiva luego de una determinado angulo de giro.

            Args:
                angulo (float): [Angulo de giro]

            Retorna True si el robot pudo hacer el giro y False en caso contrario.
        """

        print("  ⬅ izquierda")
        velocidad = 2.0
        ang_z = 0
        giro = False

        self.robot.step(self.robotTimestep)        
        obstaculo, min = self.getObstaculoAIzquierda(350)
        fls = self.frontLeftSensor.getValue()
        print("fls=",fls)

        if(obstaculo==None and fls>=self.minDistancia-0.12):
            
            giro = True
            gyroZ =self.giroscopio.getValues()[2]
            ang_z_ant=ang_z+(gyroZ*self.robotTimestep*0.001)
            pasos=0

            while ((self.robot.step(self.robotTimestep) != -1)and
                   (ang_z<(angulo))): #0.5*np.pi
                
                gyroZ =self.giroscopio.getValues()[2]
                ang_z=ang_z+(gyroZ*self.robotTimestep*0.001)
            
                self.ruedaDerechaSuperior.setVelocity(velocidad)
                self.ruedaDerechaInferior.setVelocity(velocidad)
                self.ruedaIzquierdaInferior.setVelocity(0.0)
                self.ruedaIzquierdaSuperior.setVelocity(0.0)
            
                if(ang_z==ang_z_ant):
                    paso+=1
                if(pasos == self.pasos):
                    giro=False
                    break;
                ang_z_ant = ang_z

        self.detener()

        self.mapping.update({'type': 'giro', 'value': ang_z})

        return giro
    
    def detener(self):
        """
            Permite detener al robot completamente poniendo a cero la velocidad de los motores.
            Luego de detenerse actualiza la señal.
        """

        self.robot.step(self.robotTimestep) 
        
        self.ruedaDerechaSuperior.setVelocity(0)
        self.ruedaDerechaInferior.setVelocity(0)
        self.ruedaIzquierdaInferior.setVelocity(0)
        self.ruedaIzquierdaSuperior.setVelocity(0)


        self.actualizarSenial();
#----------

#-----Acciones secundarias-----

    def avanzarObstaculo(self):
        """
            Determina la distancia al obstaculo frente al robot (utilizando el LIDAR) y avanza hasta el mismo.

            Retorna True si el robot pudo avanzar y False en caso contrario.
        """
        self.robot.step(self.robotTimestep)
        obstaculo=self.getObstaculoAlFrente(4)

        distancia = self.distAvanceMax;
        velocidad = self.speedMax
        
        avance = False

        if (obstaculo!=None):
            distancia=obstaculo[2]
            print(distancia)
        
        avance = self.avanzar(distancia, velocidad)

        return avance

    def avanzarSenial(self):
        """
            Avanza solamente si detecta una señal de radio. En cuyo caso se movera los metros equivalentes a la distancia que hay entre el robot y el emisor.

            Retorna True si el robot pudo avanzar y False en caso contrario.
        """
        self.robot.step(self.robotTimestep)
        
        avance = False

        if (self.haySenial()):
            distancia = self.distanciaSenial()
            velocidad = self.speed
            avance = self.avanzar(distancia, velocidad)
        else:
            self.detener()
        
        return avance

    def avanzarUltimaSenial(self):
        """
            Avanza la distancia almacenada en el atributo 'UltimaSenial'. En el caso que sea 'None' no se moverá.

            Retorna True si el robot pudo avanzar y False en caso contrario. 
        """
        self.robot.step(self.robotTimestep)

        avance = False

        if (self.get_ultimaSenial()!=None):
            distancia = self.get_distanciaUltimaSenial()
            velocidad = self.speed
            
            avance = self.avanzar(distancia, velocidad)
        else:
            self.detener()

        return avance

    def avanzarParaleloObstaculo(self):
        """
            Avanza paralelo al obstaculo en la orientación indicada.

            Args:
                obstaculo (integer): [1: Obstaculo a la izquierda. 2/otro: Obstaculo a la derecha]
        """
        index, distanciaDer = self.getObstaculoADerecha(40, 0.5)
        index, distanciaIzq = self.getObstaculoAIzquierda(360,0.5)

        recorrido = 0
        finaliza = True

        if(distanciaDer<distanciaIzq):
            index, distanciaDer = self.getObstaculoADerecha(10, 0.5)
            
            while((index!=None)and(finaliza)):
                if(self.getObstaculoAlFrente(0.1)==None):
                    finaliza = self.avanzar(1,5.0)
                    recorrido = recorrido + 1
                    if(recorrido>self.distAvanceMax):
                        finaliza = False
                else:
                    finaliza = False 
                
                index, distanciaDer = self.getObstaculoADerecha(10, 0.5)
        else:
            index, distanciaIzq = self.getObstaculoAIzquierda(390,0.5)
            while((index!=None)and(finaliza)):
                if(self.getObstaculoAlFrente(0.1)==None):
                    finaliza = self.avanzar(1,5.0)
                    recorrido = recorrido + 1
                    if(recorrido>self.distAvanceMax):
                        finaliza = False
                else:
                    finaliza = False 
                
                index, distanciaIzq = self.getObstaculoAIzquierda(390,0.5)
        
        return recorrido>0

    def retrocederObstaculo(self):
        """
            Determina la distancia al obstaculo trasero al robot (utilizando el LIDAR) y retrocede hasta el mismo.

            Retorna True si el robot pudo retroceder y False en caso contrario.
        """
        self.robot.step(self.robotTimestep)
        obstaculo=self.getObstaculoAtras(4)

        distancia = self.distAvanceMax;
        velocidad = self.speedMax
        
        retroceso = False

        if (obstaculo!=None):
            distancia=obstaculo[2]
            
        
        retroceso = self.retroceder(distancia, velocidad)
        return retroceso

    def giroParaleloObstaculo(self):
        """
            En el caso de que se detecte un obstaculo por el frente del robot, se procedera a girar paralelamente
            al mismo.

            Retorna True si se concreto el giro, y False en caso contrario.
        """
        giro = False
        self.robot.step(self.robotTimestep)
        ##
        obstaculo = self.getObstaculoAlFrente(0.2)
        if((obstaculo==None)and((self.get_frontLeftSensor()<self.minDistancia)or(self.get_frontRightSensor()<self.minDistancia))):
            self.retroceder(0.1,2.0)
            self.robot.step(self.robotTimestep)
            obstaculo = self.getObstaculoAlFrente(0.2)

        if(obstaculo!= None):
            if(obstaculo[0]==0):
                giro= self.giroIzquierda(0.5*np.pi)

            elif(obstaculo[1]=="right"):
                obst, min = self.getObstaculoAIzquierda(350)
                fls = self.frontLeftSensor.getValue()
                cond = ((obst==None) and (fls>=self.minDistancia-0.12))

                if(cond):
                    giro= self.giroIzquierdaParaleloObstaculo()
                
                if((not cond) or (not giro)):
                    self.retroceder(0.1,2.0)
                    giro = self.giroDerecha(-4*self.getPuntoEnRadianes(obstaculo[0]))
                    giro = self.giroDerechaParaleloObstaculo()
            else: 
                obst, min= self.getObstaculoADerecha(40)
                frs = self.frontRightSensor.getValue()
                
                cond = ((obst==None) and (frs>=self.minDistancia-0.12))

                if(cond):
                    giro= self.giroDerechaParaleloObstaculo()

                if((not cond) or (not giro)):
                    self.retroceder(0.12,2.0)
                    ang = self.getPuntoEnRadianes(360+obstaculo[0])
                    giro = self.giroIzquierda(((2*np.pi)-ang)*4)
                    giro = self.giroIzquierdaParaleloObstaculo()
        return giro
            
    def giroParaleloObstaculoGuiado(self):
        """
            En el caso de que se detecte un obstaculo por el frente del robot, se procedera a girar paralelamente
            al mismo en direccion a la ultima señal encontrada.

            Retorna True si se concreto el giro, y False en caso contrario.
        """
        obstaculo = self.getObstaculoAlFrente(0.2)
        if((obstaculo==None)and((self.get_frontLeftSensor()<self.minDistancia)or(self.get_frontRightSensor()<self.minDistancia))):
            self.retroceder(0.1,2.0)
            self.robot.step(self.robotTimestep)
            obstaculo = self.getObstaculoAlFrente(0.2)

        giro = False
            
        if(obstaculo!= None):
            direccion = self.orientacionUltimaSenial()    
            if (direccion==1):
                if(obstaculo[0]==0):
                    giro = self.giroIzquierda(0.5*np.pi)
                else:
                    self.robot.step(self.robotTimestep)

                    if(obstaculo[1]=="left"):
                        self.retroceder(0.12,2.0)
                        ang = self.getPuntoEnRadianes(360+obstaculo[0])
                        giro = self.giroIzquierda(((2*np.pi)-ang)*4)#2.4
                        giro = self.giroIzquierdaParaleloObstaculo()
                    else:
                        giro = self.giroIzquierdaParaleloObstaculo()

            elif(direccion == 2):
                if(obstaculo[0]==0):
                    giro = self.giroDerecha(-0.5*np.pi)
                else:    
                    self.robot.step(self.robotTimestep)
                        
                    if(obstaculo[1]=="right"):
                        self.retroceder(0.12,2.0)
                        giro = self.giroDerecha(-4*self.getPuntoEnRadianes(obstaculo[0]))#2.4s
                        giro = self.giroDerechaParaleloObstaculo()
                    else:
                        giro = self.giroDerechaParaleloObstaculo()
            
        return giro
                
    def giroIzquierdaParaleloObstaculo(self):
        """
            Utiliza el lidar para detectar el obstaculo más cercano del lado derecho del robot y gira hasta 
            ponerse paralelo al mismo.

            Retorna True si se concreto el giro, y False en caso contrario.
        """
        self.robot.step(self.robotTimestep)
        ##
        giro = False
        obstaculo = False

        indice, min= self.getObstaculoADerecha(0, 0.2)
        obstaculoLidar = self.getObstaculoAlFrente(0.2)

        if(obstaculoLidar!=None):
            obstaculo = obstaculoLidar[2]<self.minDistancia+0.2
        else:
            fls = self.get_frontLeftSensor()
            frs = self.get_frontRightSensor()
            obstaculo = ((fls<self.minDistancia+0.2)or(frs<self.minDistancia+0.2))
       
        if((indice!= None)and(obstaculo)):
            retrocedio= self.retroceder(0.12,2.0)
            self.robot.step(self.robotTimestep)
            indice, min= self.getObstaculoADerecha(0, 0.2)
            print("indice: ",indice)

            if((indice!= None)):
                angulo_obst = (indice) * ((2*np.pi)/400)
                angulo_giro = -(angulo_obst-(np.pi/2))
                
                giro = self.giroIzquierda(angulo_giro)

        return giro
        
    def giroDerechaParaleloObstaculo(self):
        """
            Utiliza el lidar para detectar el obstaculo más cercano del lado izquierdo del robot y gira hasta 
            ponerse paralelo al mismo.

            Retorna True si se concreto el giro, y False en caso contrario.
        """
        self.robot.step(self.robotTimestep)
        ##
        giro = False
        obstaculo = False
        indice, min= self.getObstaculoAIzquierda(400, 0.2)
        
        self.robot.step(self.robotTimestep)

        obstaculoLidar = self.getObstaculoAlFrente(0.2)
        if(obstaculoLidar!=None):
            obstaculo = obstaculoLidar[2]<self.minDistancia+0.2
        else:
            fls = self.get_frontLeftSensor()
            frs = self.get_frontRightSensor()
            obstaculo = ((fls<self.minDistancia+0.2)or(frs<self.minDistancia+0.2))
            
        print("ind: ",indice, "obst: ",obstaculo)
        
        if((indice!= None)and(obstaculo)):
            retrocedio = self.retroceder(0.12,2.0)
            self.robot.step(self.robotTimestep)
            indice, min= self.getObstaculoAIzquierda(400, 0.4)
            print("ind: ",indice)
            if((indice!= None)):
            
                angulo_obst = ((indice+300) * ((2*np.pi)/400))
                angulo_obst = (2*np.pi)-angulo_obst
                angulo_giro = angulo_obst-(np.pi/2)
            
                giro = self.giroDerecha(angulo_giro)
            
        return giro

    def giroAleatorioIzquierda(self):
        """
            Determina de forma aleatorea y uniforme un angulo de giro entre 10 y 25 grados, para posteriormente girar
            hacia la izquierda dicho valor.

            Retorna True si se concreto el giro, y False en caso contrario.
        """
        angulo = np.random.uniform(low=0.174533, high=0.125*np.pi)
        self.robot.step(self.robotTimestep)
        self.retroceder(0.05,2.0)
        giro = False
        giro = self.giroIzquierda(angulo)
        return giro

    def giroAleatorioDerecha(self):
        """
            Determina de forma aleatorea y uniforme un angulo de giro entre 10 y 25 grados, para posteriormente girar
            hacia la derecha dicho valor.

            Retorna True si se concreto el giro, y False en caso contrario.
        """
        angulo = -1*np.random.uniform(low=0.174533, high=0.125*np.pi)
        self.robot.step(self.robotTimestep)
        self.retroceder(0.05,2.0)
        giro = False
        giro = self.giroDerecha(angulo)
        return giro

    def giroSenial(self):
        """
            Busca una señal emitida y gira el robot hacia ella.

            Retorna True si se concreto el giro y False en caso contrario.
        """
        self.robot.step(self.robotTimestep)
        giro = False
        
        if (self.haySenial()):
            self.retroceder(0.1,2.0)
            direccion = self.orientacionUltimaSenial()    
            if (direccion==1):
                self.robot.step(self.robotTimestep)
                obstaculo, min = self.getObstaculoAIzquierda(360)
                if(obstaculo==None):
                    angulo = self.anguloUltimaSenial()/2
                    giro = self.giroIzquierda(angulo)
                    giro = self.giroIzquierda(angulo) #no esta repetida
            else:
                self.robot.step(self.robotTimestep)
                obstaculo, min = self.getObstaculoADerecha(40)
                if(obstaculo==None):
                    giro = self.giroDerecha(self.anguloUltimaSenial())

            return giro
        else:
            return giro
    
#----------

#----Funciones sensoriales------

#-----Mapa-----    
    def displayMapa(self):
        """
            Muestra el mapa generado a partir del recorrido.
        """
        self.mapping.display()
#----------

#-----Giroscopio-----
    def get_giroscopio(self):
        """
        Retorna el valor del giroscopio.
        """
        return self.giroscopio.getValues()
#--------

#-----Sensores infrarojos-----
    def get_frontLeftSensor(self):
        """
        Retorna el valor del sensor infrarojo frontal izquierdo.
        """
        return self.frontLeftSensor.getValue()

    def get_frontRightSensor(self):
        """
        Retorna el valor del sensor infrarojo frontal derecho.
        """
        return self.frontRightSensor.getValue()
    #
    def get_rearLeftSensor(self):
        """
        Retorna el valor del sensor infrarojo trasero izquierdo.
        """
        return self.rearLeftSensor.getValue()

    def get_rearRightSensor(self):
        """
        Retorna el valor del sensor infrarojo trasero derecho.
        """
        return self.rearRightSensor.getValue()
#----------

#-----Distancia límite a sensores infrarojos-----
    def get_limiteSensor(self):
        """
        Retorna el valor de la distancia máxima de los sensores infrarojos.
        """
        return self.limiteSensor
#----------

#-----Sensores de posicion-----
    def get_frontLeftPositionSensor(self):
        """
        Retorna el valor del sensor de posición frontal izquierdo.
        """
        return self.frontLeftPositionSensor.getValue()
    
    def get_frontRightPositionSensor(self):
        """
        Retorna el valor del sensor de posición frontal derecho.
        """
        return self.frontRightPositionSensor.getValue()
    #
    def get_rearLeftPositionSensor(self):
        """
        Retorna el valor del sensor de posición trasero izquierdo.
        """
        return self.rearLeftPositionSensor.getValue()

    def get_rearRightPositionSensor(self):
        """
        Retorna el valor del sensor de posiciónn trasero derecho.
        """
        return self.rearRightPositionSensor.getValue()
#----------

#-----Valor anterior de sensor de posicion-----
    def get_anteriorValorPositionSensor(self):
        return self.anteriorValorPositionSensor

    def DefaultPositionSensorAnterior(self):
        for i in range(1) :
            self.anteriorValorPositionSensor[i]=0
#----------

#-----Distancia recorrida-----
    def metrosRecorridos(self):
        """
        Calcura y retorna la distancia recorrida a partir de los sensores de posición y los valores de posición anteriores.
        """
        ps_values = [0, 0]
        distancia = [0, 0]
        distancia[0]=0
        distancia[1]=0
        ps_values[0] = self.frontLeftPositionSensor.getValue()-self.anteriorValorPositionSensor[0]
        ps_values[1] = self.frontRightPositionSensor.getValue()-self.anteriorValorPositionSensor[1]
        #print("position values: {} {}".format(ps_values[0],ps_values[1]))
        for i in range(2):
            distancia[i] = ps_values[i]*self.encoderUnit

        #print("metros recorridos: {} {}".format(distancia[0], distancia[1]))
        if(distancia[0] >= distancia[1]):
            self.distanciaRecorrida = self.distanciaRecorrida + distancia[0]
        else:
            self.distanciaRecorrida = self.distanciaRecorrida + distancia[1]

        return distancia;

    def metrosRecorridosHaciaAtras(self):
        """
        Calcura y retorna la distancia recorrida a partir de los sensores de posición traseros y los valores de posición anteriores.
        """
        ps_values = [0, 0]
        distancia = [0, 0]
        distancia[0]=0
        distancia[1]=0
        ps_values[0] = self.rearLeftPositionSensor.getValue()-self.anteriorValorPositionSensor[2]
        ps_values[1] = self.rearRightPositionSensor.getValue()-self.anteriorValorPositionSensor[3]
        #print("position values: {} {}".format(ps_values[0],ps_values[1]))
        for i in range(2):
            distancia[i] = ps_values[i]*self.encoderUnit

        #print("metros recorridos: {} {}".format(distancia[0], distancia[1]))

        if(distancia[0] >= distancia[1]):
            self.distanciaRecorrida = self.distanciaRecorrida + (-1*distancia[1])
        else:
            self.distanciaRecorrida = self.distanciaRecorrida + (-1*distancia[0])

        return distancia;
#----------

#-----Distancia límite a obstaculo-----
    def get_metrosColision(self):
        """
        Retorna la distancia límite al obstaculo.
        """
        return self.minDistancia

    def set_metrosColision(self, value):
        """
        Modifica la distancia límite al obstaculo.
        """
        self.minDistancia = value
#----------

#-----Receptor de señal-----            
    def get_receiver(self):
        """
        Retorna el número de paquete de datos que están actualmente en la cola del receiver.
        """
        return self.receiver.getQueueLength()
    
    def getSignalStrength(self):
        """ 
        Retorna la fuerza de la señal.
        """
        return self.receiver.getSignalStrength()
    
    def getEmitterDirection(self):
        """ 
        Retorna un vector normalizado(length=1) que indica la dirección del emisor con respecto al receptor.
        """
        punteroDireccion = self.receiver.getEmitterDirection()
        vectorDireccion = []
        for i in range(3):
            vectorDireccion.append(punteroDireccion[i])

        return vectorDireccion
#----------

#-----Calculo de Señal-----
    def distanciaSenial(self):
        """
        Retorna la distancia del receptor al emisor en base al la fuerza de la señal.

        En el simulador la fuerza de la señar es inversa a la distancia entre el emisor y receptor al cuadrado.
        r = sqrt(1/f)
        """
        return math.sqrt(1/self.getSignalStrength())

    def estimuloEncontrado(self, tolerancia):
        """
        Retorna True si esta una distancia determinada de la señal y retorna False si se encuentra a una distancia mayor a la determinada.

        La distancia se determina a partir de la distancia límite al obstaculo sumado a una tolerancia.

        Args:
            tolerancia (float): [Distancia extra a la distancia límite en la que se considera que se llego a la señal].
        """
        self.robot.step(self.robotTimestep)
        encontrado = False
        distUltimaSen = self.get_distanciaUltimaSenial()
        
        if((distUltimaSen!=None)and(distUltimaSen<=(self.get_metrosColision()+tolerancia))):
            encontrado=True
        
        if(self.haySenial()):
            if(self.distanciaSenial()<=(self.get_metrosColision()+tolerancia)):
                encontrado = True
        
        return encontrado

    def haySenial(self):
        """
            Retorna True si el número de paquetes de datos que hay en la cola del receiver es mayor a cero.
        """
        self.robot.step(self.robotTimestep)
        print(self.get_receiver())
        return self.get_receiver() > 0

    def get_ultimaSenial(self):
        """
        Retorna el valor de la dirección de la ultima señal encontrada.
        """
        return self.direccionUltimaSenial

    def set_ultimaSenial(self, value):
        """
        Actualiza el valor de la dirección de la ultima señal encontrada.

        Args:
            value (float): [Vector normalizado que indica la dirección de al emisor].
        """
        self.direccionUltimaSenial = value

    def get_distanciaUltimaSenial(self):
        """
        Retorna el valor de la distancia de la ultima señal encontrada.
        """
        return self.distanciaUltimaSenial

    def set_distanciaUltimaSenial(self, value):
        """
        Actualiza el valor de la distanci de la ultima señal encontrada.

        Args:
            value (float): [Distancia al emisor].
        """
        self.distanciaUltimaSenial = value

    def resetUltimaSenial(self):
        """
        Coloca un valor por defecto en el atributo "ultimaSenial"
        """
        self.set_ultimaSenial(None)

    def actualizarSenial(self):
        """
        Actualiza el atributo 'ultimaSenial' y 'distanciaUltimaSenial'almacenando la dirección y la distancia ultima señal encontrada respectivamente.
        """
        self.robot.step(self.robotTimestep)
        if(self.haySenial()):
            self.set_ultimaSenial(self.getEmitterDirection()) 
            self.set_distanciaUltimaSenial(self.distanciaSenial())

        self.vaciarCola();

    def vaciarCola(self):
        """
        Vacia la cola del receiver que contiene todos los paquetes recibidos hasta el momento.
        """
        while(self.get_receiver() > 0):
            self.receiver.nextPacket()

    def orientacionUltimaSenial(self):
        """
            Retorna la orientacion de la ultima señal almacenada.

            Retorno: 
                1 : señal a la izquierda.
                2 : señal a la derecha.
                3 : orientacio desconocida.
            
        """
        self.robot.step(self.robotTimestep)
        self.actualizarSenial() 
        direccion = self.get_ultimaSenial()
        giro = 3
        if(direccion!=None):
            if (direccion[0]<1):
                if(direccion[1]>0):
                    giro = 1 # 1 = izquierda
                else:
                    giro = 2 #2 = derecha
            else:
                giro=3
    
        return giro

    def anguloUltimaSenial(self):
        """
            Retorna el angulo entre el robot y la ultima señal alamacenada.
        """
        direccion = self.get_ultimaSenial()
        return math.atan2(direccion[1], direccion[0])
#----------

#-----Detección de obstaculo Sensores Infrarojos-----
    def hayObstaculo(self):
        """
        Retorna True si alguno los valores de los sensores infrarojos frontales son menores o iguales a la distancia límite al obstaculo.
        """
        min = self.minDistancia
        flsv = self.frontLeftSensor.getValue()  # Front Left Sensor Value
        frsv = self.frontRightSensor.getValue() # Front Right Sensor Value
        return (flsv <= min) or (frsv <= min)
#----------

#-----Detección de obstáculos: Lidar-----

    def getObstaculo(self,lidar_slice,extra=0):
        """
        Retorna el punto del lidar en donde se encontro la distancia mínima a un obstaculo, junto con el valor de dicha distancia.

        Args:
            lidar_slice (Array float): [Conjunto de valores de los puntos del lidar].
            extra (float): [Distancia extra a la mínima al obstaculo, por defecto cero].

        """
        min = self.minDistancia + extra
        min_index = None
        for index in range(len(lidar_slice)):
            if (0.1<lidar_slice[index] <= min)and(lidar_slice[index]>0):
                min = lidar_slice[index]
                min_index = index
        return min_index, min

    def getObstaculoAlFrente(self,extra=0):
        """
        Retorna un arreglo unidimensional de tres posiciones que nos brinda información del obstaculo en frente del lidar. 
         - En la posición cero se guarda el punto del lidar en el que se encontro la mínima distancia.
         - En la posición uno se guarda el lado ("rigth" o "left") en donde está el obstaculo.
         - En la posición dos se guarda el valor de la mínima distancia encontrada.

        El frente del lidar se definen por el atributo front_range.

        Args:
            extra (float): [Distancia extra a la mínima al obstaculo, por defecto cero].
        """
        self.robot.step(self.robotTimestep)
        lidar_data = self.lidar.getRangeImage()
        fr = self.front_range # 20
        lidar_front = lidar_data[:fr] + lidar_data[-fr:]        # mitad primera: r, mitad izq: l
        #print(lidar_front)
        obstaculo, min = self.getObstaculo(lidar_front, extra)         # Retorna el número de index y le minimo valor
        if obstaculo != None:
            if obstaculo < fr:
                lado = "right"
            else:
                lado = "left"
            return [obstaculo,lado,min]
        return None

    def getObstaculoAtras(self,extra=0):
        """
        Retorna un arreglo unidimensional de tres posiciones que nos brinda información del obstaculo en la parte trasera del lidar. 
         - En la posición cero se guarda el punto del lidar en el que se encontro la mínima distancia.
         - En la posición uno se guarda el lado ("rigth" o "left") en donde está el obstaculo.
         - En la posición dos se guarda el valor de la mínima distancia encontrada.

        La parte trasera del lidar se define por el atributo back_range.

        Args:
            extra (float): [Distancia extra a la mínima al obstaculo, por defecto cero].
        """
        self.robot.step(self.robotTimestep)
        lidar_data = self.lidar.getRangeImage()
        br = self.back_range # 25
        lidar_back = lidar_data[200-br:200+br]        # mitad primera: r, mitad izq: l
        #print(lidar_front)
        obstaculo, min = self.getObstaculo(lidar_back, extra)         # Retorna el número de index y le minimo valor
        if obstaculo != None:
            if obstaculo < 200:
                lado = "right"
            else:
                lado = "left"
            return [obstaculo,lado,min]
        return None

    def getObstaculoADerecha(self, punto_inicio, extra=0):
        """
        Retorna el punto en el que se encuentra la menor distancia al obstaculo sobre la derecha del lidar.
        
        La derecha del lidar se define desde el punto recibido por parametro hasta el punto 99 que indica los 90º
        
        Args:
            punto_inicio (integer): [Punto de inicio en el que el lidar será leido]
            extra (float): [Distancia extra a la mínima al obstaculo, por defecto cero].
        """
        self.robot.step(self.robotTimestep)
        er = self.error_range
        lidar_data = self.lidar.getRangeImage()
        lidar_right = lidar_data[punto_inicio : 99]
        obstaculo, min = self.getObstaculo(lidar_right,extra)
        return obstaculo, min

    def getObstaculoAIzquierda(self, punto_fin, extra=0):
        """
        Retorna el punto en el que se encuentra la menor distancia al obstaculo sobre la izquierda del lidar.
        
        La izquierda del lidar se define desde el punto 300 (180º) hasta el punto pasado por parametro.
        
        Args:
            punto_fin (integer): [Punto final en el que el lidar será leido]
            extra (float): [Distancia extra a la mínima al obstaculo, por defecto cero].
        """
        self.robot.step(self.robotTimestep)
        er = self.error_range
        lidar_data = self.lidar.getRangeImage()
        lidar_left = lidar_data[300:punto_fin]
        obstaculo, min = self.getObstaculo(lidar_left,extra)
        return obstaculo, min

    def getEsquinaFrontal(self):
        """
            Detecta si el robot se encuentra frente a una esquina utilizando los datos del sensor LIDAR
            y un análisis geométrico basado en RANSAC para detectar líneas en el espacio cartesiano.

            Este método convierte los datos polares del LIDAR en coordenadas cartesianas, aplica un filtro
            para descartar puntos lejanos, y luego utiliza el algoritmo RANSAC para detectar múltiples
            líneas rectas en el sector frontal. Si se detectan al menos dos líneas con un ángulo significativo
            entre ellas, y el robot se encuentra a una distancia cercana, se concluye que está frente a una esquina.

            Returns:
                bool: `True` si se detecta una esquina frontal cercana, `False` en caso contrario.

            Notas:
                - Utiliza `sklearn.linear_model.RANSACRegressor`, por lo que se debe tener instalado `scikit-learn`.
                - En caso de no contar con `scikit-learn`, el método recurre a una técnica alternativa basada en 
                detección de discontinuidades en las lecturas LIDAR.
        """
        def extract_line_segments(x, y, min_samples=12, residual_threshold=0.08, max_trials=150):
            """
                Extrae múltiples segmentos de línea del conjunto de puntos cartesianas usando el algoritmo RANSAC.

                Args:
                    x (np.ndarray): Coordenadas X de los puntos.
                    y (np.ndarray): Coordenadas Y correspondientes.
                    min_samples (int): Número mínimo de puntos necesarios para ajustar una línea válida.
                    residual_threshold (float): Umbral de tolerancia para considerar un punto como inlier.
                    max_trials (int): Número máximo de intentos de ajuste RANSAC.

                Returns:
                    List[Tuple[np.ndarray, np.ndarray, sklearn.linear_model.base.LinearRegression]]:
                        Lista de tuplas donde cada una contiene los puntos inliers en X, Y y el modelo ajustado.
                        Puede retornar una lista vacía si no se detectan líneas confiables.
            """
            
            if len(x) < min_samples:
                return []
                
            lines = []
            remaining_x = x.copy()
            remaining_y = y.copy()
            
            while len(remaining_x) >= min_samples:
                # Preparar datos para RANSAC
                X = remaining_x.reshape(-1, 1)
                y_vals = remaining_y
                
                # Ajustar línea con RANSAC
                ransac = RANSACRegressor(min_samples=min_samples, 
                                        residual_threshold=residual_threshold,
                                        max_trials=max_trials)
                try:
                    # Configurar el cálculo de score solo si hay suficientes muestras
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", category=UndefinedMetricWarning)
                        ransac.fit(X, y_vals)

                    inlier_mask = ransac.inlier_mask_
                    
                    # Si encontramos suficientes inliers, consideramos una línea válida
                    if sum(inlier_mask) >= min_samples:
                        # Extraer puntos de esta línea
                        line_x = remaining_x[inlier_mask]
                        line_y = remaining_y[inlier_mask]
                        lines.append((line_x, line_y, ransac.estimator_))
                        
                        # Remover estos puntos para la próxima iteración
                        outlier_mask = ~inlier_mask
                        remaining_x = remaining_x[outlier_mask]
                        remaining_y = remaining_y[outlier_mask]
                    else:
                        break
                except Exception as e:
                    print(f"Error en RANSAC: {e}")
                    break
                    
            return lines

        self.robot.step(self.robotTimestep)
        lidar_data_total = np.array(self.lidar.getRangeImage())
        lidar_data_total[np.isinf(lidar_data_total)] = 10  # Reemplazar "inf"
        lidar_data = np.concatenate([lidar_data_total[:40], lidar_data_total[-40:]])

        # Convertir lecturas polares a cartesianas para análisis geométrico
        num_puntos = len(lidar_data)
        angulo_incremento = 2 * np.pi / num_puntos
        puntos_x = []
        puntos_y = []
        
        for i, distancia in enumerate(lidar_data):
            if distancia <= 1:  # Filtrar puntos muy lejanos
                angulo = i * angulo_incremento
                x = distancia * np.cos(angulo)
                y = distancia * np.sin(angulo)
                puntos_x.append(x)
                puntos_y.append(y)
        
        puntos_x = np.array(puntos_x)
        puntos_y = np.array(puntos_y)
        
        # Si hay muy pocos puntos, no podemos hacer análisis confiable
        if len(puntos_x) < 10:
            return False
        
        # Intentar primero con puntos frontales (±60°)
        frontal_indices = np.concatenate([np.arange(0, num_puntos//6), np.arange(5*num_puntos//6, num_puntos)])
        frontal_x = []
        frontal_y = []
        
        for i in frontal_indices:
            if i < len(lidar_data) and lidar_data[i] < 8:
                angulo = i * angulo_incremento
                frontal_x.append(lidar_data[i] * np.cos(angulo))
                frontal_y.append(lidar_data[i] * np.sin(angulo))
        
        frontal_x = np.array(frontal_x)
        frontal_y = np.array(frontal_y)
        
        # Extraer líneas del sector frontal
        try:
            lineas_frontales = extract_line_segments(frontal_x, frontal_y)
        except ImportError:
            # Si no está disponible sklearn, usar método alternativo más simple
            # Verificar discontinuidades en las distancias
            frontal_data = np.concatenate([lidar_data[:num_puntos//6], lidar_data[5*num_puntos//6:]])
            diffs = np.abs(np.diff(frontal_data))
            discontinuidades = np.sum(diffs > 0.2)
            return discontinuidades >= 2 and np.min(frontal_data) < 0.5
        
        # Una esquina real tendrá al menos dos líneas diferentes que se intersectan
        # con un ángulo significativo en el sector frontal
        if len(lineas_frontales) >= 2:
            # Calcular ángulos entre las líneas
            coeficientes = []
            coeficientes = [line[2].coef_[0] for line in lineas_frontales]
            
            # Calcular ángulos entre líneas (en grados)
            angulos = []
            for i in range(len(coeficientes)):
                for j in range(i+1, len(coeficientes)):
                    m1, m2 = coeficientes[i], coeficientes[j]
                    if(1+m1*m2 != 0):
                        angulo = np.abs(np.arctan((m2-m1)/(1+m1*m2))) * 180/np.pi
                        angulos.append(angulo)
            
            # Si hay un ángulo significativo entre líneas (>45°), es una esquina
            esquina_detectada = any(angulo > 45 for angulo in angulos)
            
            # Verificar también que estamos cerca de la intersección
            if esquina_detectada:
                return np.min(lidar_data) < 0.75
        
        return False

    def getPuntoEnRadianes(self,index,cant_puntos=400.0):
        """
        Retorna la conversión de un punto del lidar a un angulo especifico.

        Args:
            cant_puntos (float): [Cantidad de puntos del lidar, por defecto 400].

        """
        radianes_por_punto = (2*np.pi) / float(cant_puntos)
        angulo = float(index) * radianes_por_punto
        return angulo

    def getAnguloDeGiro(self,cd_index,goal_index):
        """
        Retorna el angulo entre dos puntos del lidar.

        Args:
            cd_index (int): [Punto especifico del lidar]
            goal_index (int): [Punto objetivo]
        """
        cd_index_en_radianes = self.getPuntoEnRadianes(cd_index)
        goal_index_en_radianes = self.getPuntoEnRadianes(goal_index)
        
        radianes = cd_index_en_radianes - goal_index_en_radianes 
        
        return radianes 
#----------