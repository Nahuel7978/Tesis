import math
from controller import Robot, Camera, Motor, Receiver
from Navegacion.MapaNavegacion import *
import numpy as np

class HROSbot: 

    def __init__(self, bot):
        self.robot = bot
        self.robotTimestep = int(self.robot.getBasicTimeStep())
        self.TIMESTEP = 64
        self.speed = 5
        #
        self.ruedaDerechaSuperior = self.robot.getDevice("fr_wheel_joint")
        self.ruedaDerechaInferior = self.robot.getDevice("rr_wheel_joint")
        self.ruedaIzquierdaSuperior = self.robot.getDevice("fl_wheel_joint")
        self.ruedaIzquierdaInferior = self.robot.getDevice("rl_wheel_joint")
        #
        self.ruedaDerechaSuperior.setPosition(float('inf'))
        self.ruedaDerechaInferior.setPosition(float('inf'))
        self.ruedaIzquierdaInferior.setPosition(float('inf'))
        self.ruedaIzquierdaSuperior.setPosition(float('inf'))
        #
        self.giroscopio = self.robot.getDevice("imu gyro")
        self.acelerometro = self.robot.getDevice("imu accelerometer")
        self.lidar = self.robot.getDevice("laser")
        #
        self.giroscopio.enable(self.robotTimestep)
        self.acelerometro.enable(self.robotTimestep)
        self.lidar.enable(self.robotTimestep)
        #
        self.frontLeftSensor = self.robot.getDevice("fl_range")
        self.frontRightSensor = self.robot.getDevice("fr_range")
        self.rearLeftSensor = self.robot.getDevice("rl_range")
        self.rearRightSensor = self.robot.getDevice("rr_range")
        #
        self.frontLeftSensor.enable(self.robotTimestep)
        self.frontRightSensor.enable(self.robotTimestep)
        self.rearLeftSensor.enable(self.robotTimestep)
        self.rearRightSensor.enable(self.robotTimestep)
        #
        self.frontLeftPositionSensor = self.robot.getDevice("front left wheel motor sensor")
        self.frontRightPositionSensor = self.robot.getDevice("front right wheel motor sensor")
        self.rearLeftPositionSensor = self.robot.getDevice("rear left wheel motor sensor")
        self.rearRightPositionSensor = self.robot.getDevice("rear right wheel motor sensor")
        #
        self.frontLeftPositionSensor.enable(self.TIMESTEP)
        self.frontRightPositionSensor.enable(self.TIMESTEP)
        self.rearLeftPositionSensor.enable(self.TIMESTEP)
        self.rearRightPositionSensor.enable(self.TIMESTEP)
        #
        self.anteriorValorPositionSensor = [0,0]
        self.DefaultPositionSensorAnterior()
        self.limiteSensor = 2.0
        # Detección de obstáculos
        self.minDistancia = 0.3
        self.toleranciaEntreSensores = 0.05
        self.epsilon = 0.01
        self.error_range = 3
        self.front_range = 25
        self.goal_index = 100
        self.left_goal_index = 300
        self.minSignal = 0.5
        # 
        #
        self.radioRueda = 0.0425
        self.encoderUnit = (2*np.pi*self.radioRueda)/6.28 
        #
        self.receiver = self.robot.getDevice('Receiver')
        #
        self.receiver.enable(32)
        self.direccionUltimaSenial = None
        self.distanciaUltimaSenial = None
        #
        self.mapping = MapaNavegacion(self)
 
    def avanzar(self, distancia, velocidad):
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

            
        self.ruedaDerechaSuperior.setVelocity(0)
        self.ruedaDerechaInferior.setVelocity(0)
        self.ruedaIzquierdaInferior.setVelocity(0)
        self.ruedaIzquierdaSuperior.setVelocity(0)
        self.anteriorValorPositionSensor[0] = self.frontLeftPositionSensor.getValue()
        self.anteriorValorPositionSensor[1] = self.frontRightPositionSensor.getValue()
        
        self.mapping.update({'type': 'avance', 'value': max(dist)})

        if((dist[0]>=distancia) or (dist[1]>=distancia)):
            return True
        else:
            return False

    def retroceder(self, distancia, velocidad):
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
            
        self.ruedaDerechaSuperior.setVelocity(0)
        self.ruedaDerechaInferior.setVelocity(0)
        self.ruedaIzquierdaInferior.setVelocity(0)
        self.ruedaIzquierdaSuperior.setVelocity(0)
        
        if((dist[0]<=distancia) or (dist[1]<=distancia)):
            return True
        else:
            return False
    

    def giroDerecha(self, angulo):
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
                
            
        self.ruedaDerechaSuperior.setVelocity(0)
        self.ruedaDerechaInferior.setVelocity(0)
        self.ruedaIzquierdaInferior.setVelocity(0)
        self.ruedaIzquierdaSuperior.setVelocity(0)

        self.mapping.update({'type': 'giro', 'value': ang_z})

        return giro

    def giroIzquierda(self, angulo):
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
            
        self.ruedaDerechaSuperior.setVelocity(0)
        self.ruedaDerechaInferior.setVelocity(0)
        self.ruedaIzquierdaInferior.setVelocity(0)
        self.ruedaIzquierdaSuperior.setVelocity(0)

        self.mapping.update({'type': 'giro', 'value': ang_z})

        return giro

#-----    
    def DisplayData(self,step):
        print("STEP #",step)
        print("   Acelerómetro: ", self.acelerometro.getValues())
        print("   Giroscopio:   ", self.giroscopio.getValues())
        print("   Sensores infrarrojos de distancia:")
        print("       L: ",self.frontLeftSensor.getValue(),"; R: ",self.frontRightSensor.getValue())
        print("   Hay Obstáculo: ",(self.frontLeftSensor.getValue() < self.minDistancia or self.frontRightSensor.getValue() < self.minDistancia))
        print("   Hay Señal:    ", self.haySeñal())
    
    def displayMapa(self):
        self.mapping.display()

    #-> Sensores de colision
    def get_frontLeftSensor(self):
        return self.frontLeftSensor.getValue()

    def get_frontRightSensor(self):
        return self.frontRightSensor.getValue()
    #
    def get_rearLeftSensor(self):
        return self.rearLeftSensor.getValue()

    def get_rearRightSensor(self):
        return self.rearRightSensor.getValue()
    
    #-> Sensores de posicion
    def get_frontLeftPositionSensor(self):
        return self.frontLeftPositionSensor.getValue()
    
    def get_frontRightPositionSensor(self):
        return self.frontRightPositionSensor.getValue()
    #
    def get_rearLeftPositionSensor(self):
        return self.rearLeftPositionSensor.getValue()

    def get_rearRightPositionSensor(self):
        return self.rearRightPositionSensor.getValue()
    
    def metrosRecorridos(self):
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
    
    #-> Limite de sensores de colision
    def get_limiteSensor(self):
        return self.limiteSensor
    
    #Metros de colision
    def get_metrosColision(self):
        return self.minDistancia

    def set_metrosColision(self, value):
        self.minDistancia = value
    
    #Valor anterior de sensor de posicion
    def get_anteriorValorPositionSensor(self):
        return self.anteriorValorPositionSensor

    def DefaultPositionSensorAnterior(self):
        for i in range(1) :
            self.anteriorValorPositionSensor[i]=0

    def hayObstaculo(self):
        min = self.minDistancia
        flsv = self.frontLeftSensor.getValue()  # Front Left Sensor Value
        frsv = self.frontRightSensor.getValue() # Front Right Sensor Value
        return (flsv <= min) or (frsv <= min)

    #-> Receiver            
    def get_receiver(self):
        return self.receiver.getQueueLength()
    
    def getSignalStrength(self):
        return self.receiver.getSignalStrength()
    
    def getEmitterDirection(self):
        return self.receiver.getEmitterDirection()
    
    def distanciaSeñal(self):
        return math.sqrt(1/self.getSignalStrength())
    
    def estimuloEncontrado(self, tolerancia):
        self.robot.step(self.robotTimestep)
        encontrado = False
        distUltimaSen = self.get_distanciaUltimaSenial()
        
        if((distUltimaSen!=None)and(distUltimaSen<=(self.minDistancia+tolerancia))):
            encontrado=True
        
        if(self.get_receiver() > 0):
            if(self.distanciaSeñal()<=(self.minDistancia+tolerancia)):
                encontrado = True
        
        return encontrado

    def haySeñal(self):
        return self.receiver.getQueueLength() > 0

    def actualizarSeñal(self):
        self.robot.step(self.robotTimestep)
        if(self.haySeñal()):
            self.set_ultimaSeñal(self.getEmitterDirection()) 
            self.set_distanciaUltimaSenial(self.distanciaSeñal())

    def resetUltimaSeñal(self):
        self.set_ultimaSeñal(None)

    def get_ultimaSeñal(self):
        return self.direccionUltimaSenial

    def set_ultimaSeñal(self, value):
        self.direccionUltimaSenial = value

    def get_distanciaUltimaSenial(self):
        return self.distanciaUltimaSenial

    def set_distanciaUltimaSenial(self, value):
        self.distanciaUltimaSenial = value

    def vaciarCola(self):
        while(self.receiver.getQueueLength() > 0):
            self.receiver.nextPacket()
    
   #-> Detección de obstáculos: Lidar

    def getObstaculo(self,lidar_slice,extra=0):
        min = self.minDistancia + extra
        min_index = None
        for index in range(len(lidar_slice)):
            if (lidar_slice[index] <= min)and(lidar_slice[index]>0):
                min = lidar_slice[index]
                min_index = index
        return min_index, min

    def getObstaculoAlFrente(self,extra=0):
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
        self.robot.step(self.robotTimestep)
        er = self.error_range
        lidar_data = self.lidar.getRangeImage()
        lidar_right = lidar_data[35 : 99]
        obstaculo, min = self.getObstaculo(lidar_right,0.2+extra)
        return obstaculo

    def getObstaculoAIzquierda(self,extra=0):
        self.robot.step(self.robotTimestep)
        er = self.error_range
        lidar_data = self.lidar.getRangeImage()
        lidar_left = lidar_data[300:365]
        obstaculo, min = self.getObstaculo(lidar_left,0.2+extra)
        return obstaculo
    
    def getPuntoEnRadianes(self,index,cant_puntos=400.0):
        radianes_por_punto = (2*np.pi) / float(cant_puntos)
        angulo = float(index) * radianes_por_punto
        return angulo

    def getAnguloDeGiro(self,cd_index,goal_index):
        cd_index_en_radianes = self.getPuntoEnRadianes(cd_index)
        goal_index_en_radianes = self.getPuntoEnRadianes(goal_index)
        
        radianes = abs( cd_index_en_radianes - goal_index_en_radianes )
        print(cd_index_en_radianes,"-",goal_index_en_radianes,"=",radianes)
        return radianes 
    
    #-> Giroscopio
    def get_giroscopio(self):
        return self.giroscopio.getValues()
    #---
""""

    ###
    
    def get_robotTimestep(self):
        return self.robotTimestep

    def set_robotTimestep(self, value):
        self.robotTimestep = value

    def get_TIMESTEP(self):
        return self.TIMESTEP

    def set_TIMESTEP(self, value):
        self.TIMESTEP = value

    

    def get_acelerometro(self):
        return self.acelerometro

    


"""