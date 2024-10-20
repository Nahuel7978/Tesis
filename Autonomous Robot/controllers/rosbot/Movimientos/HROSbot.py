import math
from controller import Robot, Camera, Motor, Receiver
from Navegacion.MapaNavegacion import *
import numpy as np

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

        self.distAvanceMax = 4
        self.distAvanceMedio = 2
        self.distAvanceMin = 1

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

        self.front_range = 20
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

        self.anteriorValorPositionSensor = [0,0]
        self.DefaultPositionSensorAnterior()

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
 
 #-----Acciones primarias-----
    def avanzar(self, distancia, velocidad):
        """ 
            Permite avanzar al robot. 

            Activa los motores de las ruedas a una determinada velocidad y los desactiva luego de una determinada distancia.
            Avanza siempre y cuando no detecte un obstaculo en frente con el lidar.

            Args:
                distancia (float): [Distancia]
                velociada (float): [Velocidad]
        """
        print("  ⬆ Avanzar")
        dist = [0, 0]
        dist[0] = 0
        dist[1] = 0

        self.robot.step(self.robotTimestep)

        while ((self.getObstaculoAlFrente()==None)and
               (dist[0]<distancia or dist[1]<distancia)and
               (self.robot.step(self.robotTimestep) != -1)):
            dist =  self.metrosRecorridos()
            self.ruedaDerechaSuperior.setVelocity(velocidad)
            self.ruedaDerechaInferior.setVelocity(velocidad)
            self.ruedaIzquierdaInferior.setVelocity(velocidad)
            self.ruedaIzquierdaSuperior.setVelocity(velocidad)
    
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
        """

        print("  ⬇ Retroceder")
        dist = [0, 0]
        distancia = -1*distancia
        self.robot.step(self.robotTimestep)
        self.anteriorValorPositionSensor[0] = self.frontLeftPositionSensor.getValue()
        self.anteriorValorPositionSensor[1] = self.frontRightPositionSensor.getValue()

        rls = self.rearLeftSensor.getValue()
        rrs = self.rearRightSensor.getValue()

        dist[0] = 0
        dist[1] = 0

        if((rls>distancia and rrs>distancia)):
            while ((dist[0]>distancia or dist[1]>distancia)and
                   (self.robot.step(self.robotTimestep) != -1)and
                   (rls>distancia and rrs>distancia)):
                
                dist =  self.metrosRecorridos()
                self.ruedaDerechaSuperior.setVelocity(-velocidad)
                self.ruedaDerechaInferior.setVelocity(-velocidad)
                self.ruedaIzquierdaInferior.setVelocity(-velocidad)
                self.ruedaIzquierdaSuperior.setVelocity(-velocidad)
                rls = self.rearLeftSensor.getValue()
                rrs = self.rearRightSensor.getValue()
            
        self.detener()
        
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
        """
        print("  ⮕ Derecha")
        velocidad = 2.0
        ang_z = 0
        giro = False

        self.robot.step(self.robotTimestep)
        lidar_data = self.lidar.getRangeImage()
        lidar_right = lidar_data[25:99]
        obstaculo, min = self.getObstaculo(lidar_right)
        if(obstaculo==None):
            giro = True
            while ((self.robot.step(self.robotTimestep) != -1)and
                   (ang_z>(angulo))):
                gyroZ =self.giroscopio.getValues()[2]
                ang_z=ang_z+(gyroZ*self.robotTimestep*0.001)
            
                self.ruedaDerechaSuperior.setVelocity(0.0)
                self.ruedaDerechaInferior.setVelocity(0.0)
                self.ruedaIzquierdaInferior.setVelocity(velocidad)
                self.ruedaIzquierdaSuperior.setVelocity(velocidad)
                
        self.detener()

        self.mapping.update({'type': 'giro', 'value': ang_z})

        return giro

    def giroIzquierda(self, angulo):
        """ 
            Permite girar hacia la derecha al robot. 

            Activa los motores derechos de las ruedas a una velocidad predefinida y los desactiva luego de una determinado angulo de giro.

            Args:
                angulo (float): [Angulo de giro]
        """

        print("  ⬅ izquierda")
        velocidad = 2.0
        ang_z = 0
        giro = False

        self.robot.step(self.robotTimestep)        
        lidar_data = self.lidar.getRangeImage()
        lidar_left = lidar_data[300:375]
        obstaculo, min = self.getObstaculo(lidar_left)

        if(obstaculo==None):
            
            giro = True

            while ((self.robot.step(self.robotTimestep) != -1)and
                   (ang_z<(angulo))): #0.5*np.pi
                
                gyroZ =self.giroscopio.getValues()[2]
                ang_z=ang_z+(gyroZ*self.robotTimestep*0.001)
            
                self.ruedaDerechaSuperior.setVelocity(velocidad)
                self.ruedaDerechaInferior.setVelocity(velocidad)
                self.ruedaIzquierdaInferior.setVelocity(0.0)
                self.ruedaIzquierdaSuperior.setVelocity(0.0)
            
        self.detener()

        self.mapping.update({'type': 'giro', 'value': ang_z})

        return giro
    
    def detener(self):
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
        """
        self.robot.step(self.robotTimestep)
        obstaculo=self.getObstaculoAlFrente(4)

        distancia = self.distAvanceMax;
        velocidad = self.speedMax
        
        if (obstaculo!=None):
            distancia=obstaculo[2]
            print(distancia)
        
        self.avanzar(distancia, velocidad)

    def avanzarSenial(self):
        """
            Avanza solamente si detecta una señal de radio. En cuyo caso se movera los metros equivalentes a la distancia que hay entre el robot y el emisor.
        """
        self.vaciarCola()
        self.robot.step(self.robotTimestep)
        print(self.haySenial())
        if (self.haySenial()):
            distancia = self.distanciaSenial()
            velocidad = self.speed
            print("Distancia: ",distancia)
            self.avanzar(distancia, velocidad)
        else:
            self.detener()

    def avanzarUltimaSenial(self):
        """
            Avanza la distancia almacenada en el atributo 'UltimaSenial'. En el caso que sea 'None' no se moverá.
        """
        self.robot.step(self.robotTimestep)
        if (self.get_ultimaSenial()!=None):
            distancia = self.get_distanciaUltimaSenial()
            velocidad = self.speed
            print("Distancia: ",distancia)
            self.avanzar(distancia, velocidad)
        else:
            self.detener()

    def giroIzquierdoParaleloObstaculo(self):
        self.robot.step(self.robotTimestep)
        self.giroIzquierda(0.5*np.pi)

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
        
        if(self.get_receiver() > 0):
            if(self.distanciaSenial()<=(self.get_metrosColision()+tolerancia)):
                encontrado = True
        
        return encontrado

    def haySenial(self):
        """
            Retorna True si el número de paquetes de datos que hay en la cola del receiver es mayor a cero.
        """
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
            if (lidar_slice[index] <= min)and(lidar_slice[index]>0):
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
        fr = self.front_range # 25
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

    def getObstaculoADerecha(self,extra=0):
        """
        Retorna el punto en el que se encuentra la menor distancia al obstaculo sobre la derecha del lidar.
        
        El derecha del lidar se define por los puntos que van del [35, 99].
        
        Args:
            extra (float): [Distancia extra a la mínima al obstaculo, por defecto cero].
        """
        self.robot.step(self.robotTimestep)
        er = self.error_range
        lidar_data = self.lidar.getRangeImage()
        lidar_right = lidar_data[35 : 99]
        obstaculo, min = self.getObstaculo(lidar_right,0.2+extra)
        return obstaculo

    def getObstaculoAIzquierda(self,extra=0):
        """
        Retorna el punto en el que se encuentra la menor distancia al obstaculo sobre la izquierda del lidar.
        
        El derecha del lidar se define por los puntos que van del [300, 365].
        
        Args:
            extra (float): [Distancia extra a la mínima al obstaculo, por defecto cero].
        """
        self.robot.step(self.robotTimestep)
        er = self.error_range
        lidar_data = self.lidar.getRangeImage()
        lidar_left = lidar_data[300:365]
        obstaculo, min = self.getObstaculo(lidar_left,0.2+extra)
        return obstaculo

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
        
        radianes = abs( cd_index_en_radianes - goal_index_en_radianes )
        print(cd_index_en_radianes,"-",goal_index_en_radianes,"=",radianes)
        return radianes 
#----------