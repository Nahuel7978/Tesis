import math
from controller import Robot, Camera, Motor, Receiver, Supervisor
import numpy as np
from deepbots.supervisor.controllers.robot_supervisor_env import RobotSupervisorEnv
from gym.spaces import Box,Discrete

class RobotController(RobotSupervisorEnv): 
    """
    Representa al robot Husuarion Rosbot.
    """
    def __init__(self):
        """
           Inicializa un objeto de tipo HROSbot.

            Habilita los dispositivos del robot.
        """

        #---Inicialización.
        
        super().__init__()
        
        #--- Parametros de entrenamiento
        obs_space=403
        act_space=3
        self.observation_space = Box(low=-np.inf, high=np.inf, shape=(obs_space,), dtype=np.float32)
        self.action_space = Discrete(act_space)
        self.obs_space = obs_space
        self.act_space= act_space

        #---Atributos.
        self.speedMax = 8
        self.speed = 5
        self.speedMin = 2

        self.distAvanceMax = 3
        self.distAvanceMedio = 2
        self.distAvanceMin = 1

        self.pasos = 200

        self.ant_val_pos = [0.0, 0.0]  # [izq, der]
        self.ant_dist_senial = None
        self.ant_angulo = None
        
        #---Robot timestep.
        self.robotTimestep = self.timestep

        #---Activación de moteres.
        self.ruedaDerechaSuperior = self.getDevice("fr_wheel_joint")
        self.ruedaDerechaInferior = self.getDevice("rr_wheel_joint")
        self.ruedaIzquierdaSuperior = self.getDevice("fl_wheel_joint")
        self.ruedaIzquierdaInferior = self.getDevice("rl_wheel_joint")

        self.ruedaDerechaSuperior.setPosition(float('inf'))
        self.ruedaDerechaInferior.setPosition(float('inf'))
        self.ruedaIzquierdaInferior.setPosition(float('inf'))
        self.ruedaIzquierdaSuperior.setPosition(float('inf'))

        #---Activación de giroscopio.
        self.giroscopio = self.getDevice("imu gyro")
        self.giroscopio.enable(self.robotTimestep)

        #---Activación de acelerometro.
        self.acelerometro = self.getDevice("imu accelerometer")
        self.acelerometro.enable(self.robotTimestep)

        #---Activación del lidar-
        self.lidar = self.getDevice("laser")
        self.lidar.enable(self.robotTimestep)
        self.lidar.enablePointCloud()

        self.front_range = 25
        self.back_range = 25
        self.error_range = 3

        #---Activación de Sensores infrarojos.
        self.frontLeftSensor = self.getDevice("fl_range")
        self.frontRightSensor = self.getDevice("fr_range")
        self.rearLeftSensor = self.getDevice("rl_range")
        self.rearRightSensor = self.getDevice("rr_range")
        
        self.frontLeftSensor.enable(self.robotTimestep)
        self.frontRightSensor.enable(self.robotTimestep)
        self.rearLeftSensor.enable(self.robotTimestep)
        self.rearRightSensor.enable(self.robotTimestep)

        self.limiteSensor = 2.0
        self.minDistancia = 0.3

        #---Activación de sensores de posición.
        self.frontLeftPositionSensor = self.getDevice("front left wheel motor sensor")
        self.frontRightPositionSensor = self.getDevice("front right wheel motor sensor")
        self.rearLeftPositionSensor = self.getDevice("rear left wheel motor sensor")
        self.rearRightPositionSensor = self.getDevice("rear right wheel motor sensor")
        
        self.frontLeftPositionSensor.enable(self.robotTimestep)
        self.frontRightPositionSensor.enable(self.robotTimestep)
        self.rearLeftPositionSensor.enable(self.robotTimestep)
        self.rearRightPositionSensor.enable(self.robotTimestep)

        self.anteriorValorPositionSensor = [0,0,0,0]

        self.distanciaRecorrida = 0

        #---Activación Receiver
        self.receptor = self.getDevice('Receiver')
        self.receptor.enable(self.robotTimestep)

        self.direccionUltimaSenial = None
        self.distanciaUltimaSenial = None

        #---Atributos propios de las ruedas.
        self.radioRueda = 0.0425
        self.encoderUnit = (2*np.pi*self.radioRueda)/6.28 
        
        #--- Parámetros de recompensa
        self.recompensa_maxima = 5
        self.recompensa_minima = 1
        self.penalizacion_maxima = -5
        self.penalizacion_minima = 1
        self.tolerancia_movimiento = 1

        #--- Parámetros de reseteo.
        name="principal_robot"
        self.robot_node = self.getFromDef(name)
        if self.robot_node is None:
            raise RuntimeError("No se encontró el robot con DEF=",name)
        self.translation = self.robot_node.getField("translation")
        self.rotation = self.robot_node.getField("rotation")
        self.startPoints = []
        self.startRotation = []
        self.startPoints.append(self.currentLocation())
        self.startRotation.append(self.currentRotation())
        
        #---
        self.detener()
        self.defaultPositionSensorAnterior()

#-----Deepbots-----

    def get_observations(self):
        lidar_data = np.array(self.lidar.getRangeImage())
        lidar_data[np.isinf(lidar_data)] = 10
        lidar_data[np.isnan(lidar_data)] = 0
        signal_strength = 0.0
        distance = 0.0
        angle = 0.0
        if(self.haySenial()):
            signal_strength = self.getSignalStrength()
            distance = self.distanciaSenial()
            angle = self.anguloUltimaSenial()
            if not self.is_done():
                self.startPoints.append(self.currentLocation())
                self.startRotation.append(self.currentRotation())
        observations = lidar_data.tolist() + [signal_strength,distance,angle]
        return np.array(observations, dtype=np.float32)

    def get_default_observation(self):
        return np.zeros(self.obs_space, dtype=np.float32)

    def get_reward(self,action):
        act_val_pos_der = round(self.frontRightPositionSensor.getValue(), 1)
        act_val_pos_izq = round(self.frontLeftPositionSensor.getValue(), 1)
        senal = self.haySenial()
        recompensa = 0

        # 1. VERIFICAR MOVIMIENTO
        movimiento = not ((self.ant_val_pos[0] + self.tolerancia_movimiento > act_val_pos_izq) and 
                         (self.ant_val_pos[1] + self.tolerancia_movimiento > act_val_pos_der))
        if not movimiento:
            print("|-> Recompensa (sin movimiento): ", self.penalizacion_maxima)
            self.ant_val_pos[0] = act_val_pos_izq
            self.ant_val_pos[1] = act_val_pos_der
            return self.penalizacion_maxima
        
        # 2. SI HAY SEÑAL
        if (senal):
            tolerancia = 0.5
            
            # RECOMPENSA MÁXIMA: Meta alcanzada
            if self.estimuloEncontrado(tolerancia):
                print("|-> Recompensa (meta alcanzada): ", self.recompensa_maxima)
                self.ant_val_pos[0] = act_val_pos_izq
                self.ant_val_pos[1] = act_val_pos_der
                return self.recompensa_maxima
            
            # Datos actuales
            act_dist_senial = self.distanciaSenial()
            act_angulo = self.anguloUltimaSenial()
            
            # 2.1. Recompensa por acercarse
            if self.ant_dist_senial is not None:
                delta_distancia = self.ant_dist_senial - act_dist_senial
                if delta_distancia > 0:  # Se acercó
                    recompensa += self.recompensa_minima * (1 + delta_distancia)
                else:  # Se alejó
                    recompensa += self.penalizacion_minima * (1 - delta_distancia)

            # 2.2. Recompensa por orientación correcta
            orientacion_robot = self.get_orientacion_robot()      
            
            # Diferencia entre orientación del robot y dirección hacia la señal
            diferencia_angular = abs(orientacion_robot - act_angulo)

            # Normalizar a [0, π]
            if diferencia_angular > math.pi:
                diferencia_angular = 2 * math.pi - diferencia_angular
            
            # Recompensa por buena orientación
            if diferencia_angular < math.pi / 6:  # < 30°
                recompensa += 0.2
            elif diferencia_angular < math.pi / 3:  # < 60°
                recompensa += 0.1
            else:  # > 60°
                recompensa -= 0.1

            # 2.3. Recompensa por mejorar orientación
            if self.ant_angulo is not None:
                delta_orientacion = abs(self.ant_angulo - act_angulo)
                if delta_orientacion < 0.1:  # Se mantiene bien orientado
                    recompensa += 0.05
            
            # Actualizar estado anterior para la próxima iteración
            self.ant_dist_senial = act_dist_senial
            self.ant_angulo = act_angulo
        # 3. SIN SEÑAL
        else:
            recompensa = self.penalizacion_minima * 0.5

        self.ant_val_pos[0] = act_val_pos_izq
        self.ant_val_pos[1] = act_val_pos_der
        print("|-> Recompensa: ", recompensa)
        return recompensa
    
    def is_done(self):
        return self.estimuloEncontrado(0.5)

    def get_info(self):
        """
        This method can be implemented to return any diagnostic
        information on each step, e.g. for debugging purposes.
        """
        return {"done": self.is_done()}

    def apply_action(self, action):
        self.activateRobotTimestep()

        if(action==0):
            self.ir_estimulo()
        elif(action==1):
            self.evitarObstaculo()
        elif(action==2):
            self.explorar()
        else: 
            raise ValueError(f"Acción no válida: {action}")
        
        
        self.detener()

    def reset(self):    
        if(self.is_done()==True):
            index = np.random.randint(0,len(self.startPoints))
            self.translation.setSFVec3f(self.startPoints[index])
            self.rotation.setSFRotation(self.startRotation[index])
            self.done='False'
            self.default()
            self.simulationResetPhysics()
            super(Supervisor, self).step(int(self.getBasicTimeStep()))
            return self.get_default_observation()

        
        return self.get_observations()

    def render(self, mode="human"):
        pass
#----------

#-----Comportamientos-----   
    def ir_estimulo(self):
        """
            Busca la señal de un Emmiter y en caso de encontrarla orienta el robot hacia la misma y avanza la distancia que hay entre él y el emisor.

        """
        ##self.updateTimestep()
        print("-----> Ir_estimulo")
        velocidad = self.speedMax
        finaliza = False
        giro = False

        giro = self.giroSenial()
        ##print("giro: ",giro)
        if(giro):
            finaliza = self.avanzarSenial()
            
        self.vaciarCola()
            
        return finaliza

    def evitarObstaculo(self):
        """
            Evita un obstaculo girando en dirección a la última señal encontrada.
            En caso de no poder hacerlo evita el obstaculo en base al angulo del obstaculo encontrado.
        """
        
        ##self.updateTimestep()
        self.vaciarCola()
        print("--> Evitar Obstaculo")
        obstaculo =  self.getObstaculoAlFrente(0.3)
        giro = False
        finaliza = False
        #print("obstaculo: ", obstaculo)
        if((obstaculo != None)or((self.get_frontLeftSensor()<self.minDistancia)or(self.get_frontRightSensor()<self.minDistancia))):
            self.retroceder(0.05,2)
            
            if(self.get_ultimaSenial()!=None):
                giro = self.giroParaleloObstaculoGuiado()

            if(not giro):
                giro = self.giroParaleloObstaculo()
            
            self.actualizarSenial()
            if(giro):
                finaliza = self.avanzarParaleloObstaculo()
            else:
                finaliza = False

        self.vaciarCola()
        #self.robot.step(self.robotTimestep)
        return finaliza

    def explorar(self):
        """
            Explora el entorno decidiendo de forma aleatoria si girar o no. 
            - Si gira, lo hace en base a la ultima señal detectada.
        """
        print("--> Explorar")
        #self.robot.step(self.robotTimestep)
        self.vaciarCola()
        velocidad = self.speedMax
        distancia = 1

        ##if (not self.haySenial()):
        self.exploracion = True
        probMov = np.random.uniform()
        giro = False
        avance = False

        if((probMov<=0.7)):
            gDeterminado = self.orientacionUltimaSenial()
            i = 0
            while((not giro)and(i<=1)):
                i +=1
                if(gDeterminado==1):
                    #self.robot.step(self.robotTimestep)
                    giro = self.giroAleatorioIzquierda()
                   
                    if(not giro):
                        gDeterminado = 2
                else:
                    #self.robot.step(self.robotTimestep)
                    giro = self.giroAleatorioDerecha()

                    if(not giro):
                        gDeterminado = 1
                           
        if(probMov<=0.3):
            distancia=2

        avance = self.avanzar(distancia,velocidad) 
        
        self.exploracion=False

        return (giro or avance)

#----------
 
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
        #print("  ⬆ Avanzar")
        dist = [0, 0]
        dist[0] = 0
        dist[1] = 0

        
        fls = self.frontLeftSensor.getValue()
        frs = self.frontRightSensor.getValue()
        
        if(fls>self.minDistancia and frs>self.minDistancia):
            dist_ant=self.metrosRecorridos()
            p = 0

            while ((self.getObstaculoAlFrente()==None)and
                (dist[0]<distancia or dist[1]<distancia)):
                dist =  self.metrosRecorridos()
                self.ruedaDerechaSuperior.setVelocity(velocidad)
                self.ruedaDerechaInferior.setVelocity(velocidad)
                self.ruedaIzquierdaInferior.setVelocity(velocidad)
                self.ruedaIzquierdaSuperior.setVelocity(velocidad)
                self.updateTimestep()
                
                if(dist==dist_ant):
                    p+=1
                if(p == self.pasos):
                    #print("pasos: ",p < self.pasos," dist:",dist)
                    break;
                
                dist_ant = dist
        #self.detener()

        
 
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

        #print("  ⬇ Retroceder")
        dist = [0, 0]
        distancia = -1*distancia
        #self.robot.step(self.robotTimestep)
        self.anteriorValorPositionSensor[2] = self.rearLeftPositionSensor.getValue()
        self.anteriorValorPositionSensor[3] = self.rearRightPositionSensor.getValue()


        rls = self.rearLeftSensor.getValue()
        rrs = self.rearRightSensor.getValue()
        dist[0] = 0
        dist[1] = 0
        
        if(rls>(self.minDistancia-0.2) and rrs>(self.minDistancia-0.2)):
            pasos= 0
            dist_ant = self.metrosRecorridosHaciaAtras()
            while ((dist[0]>distancia or dist[1]>distancia)):
                
                #dist =  self.metrosRecorridos()
                dist = self.metrosRecorridosHaciaAtras()
                self.ruedaDerechaSuperior.setVelocity(-velocidad)
                self.ruedaDerechaInferior.setVelocity(-velocidad)
                self.ruedaIzquierdaInferior.setVelocity(-velocidad)
                self.ruedaIzquierdaSuperior.setVelocity(-velocidad)
                self.updateTimestep()
                if(dist==dist_ant):
                    pasos+=1

                if(pasos == self.pasos):
                    break;
                
                dist_ant = dist

                
        #self.detener()
        

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
        #print("  ⮕ Derecha")
        velocidad = 2.0
        ang_z = 0
        giro = False

        #self.robot.step(self.robotTimestep)
        obstaculo, min= self.getObstaculoADerecha(10)
        frs = self.frontLeftSensor.getValue()
        #print(min,">=", " and ", frs,">=",self.minDistancia-0.12)
        #print("angulo=",angulo)
        if((obstaculo==None or min>=self.minDistancia-0.12) and frs>=self.minDistancia-0.12):
            giro = True
            ant_gyroZ =self.giroscopio.getValues()[2]
            pasos=0
            
            while ((ang_z>(angulo)) and frs>=self.minDistancia-0.12):
                
                gyroZ =self.giroscopio.getValues()[2]
                ang_z=ang_z+(gyroZ*self.robotTimestep*0.001)
                
                self.ruedaDerechaSuperior.setVelocity(0.0)
                self.ruedaDerechaInferior.setVelocity(0.0)
                self.ruedaIzquierdaInferior.setVelocity(velocidad)
                self.ruedaIzquierdaSuperior.setVelocity(velocidad)
                self.updateTimestep()
                frs = self.frontLeftSensor.getValue()
                
                if(gyroZ==ant_gyroZ):
                    pasos+=1
                if(pasos == self.pasos):
                    giro=False
                    break;
                
                ant_gyroZ = gyroZ
                
        #self.detener()

        
        return giro

    def giroIzquierda(self, angulo):
        """ 
            Permite girar hacia la derecha al robot. 

            Activa los motores derechos de las ruedas a una velocidad predefinida y los desactiva luego de una determinado angulo de giro.

            Args:
                angulo (float): [Angulo de giro]

            Retorna True si el robot pudo hacer el giro y False en caso contrario.
        """

        #print("  ⬅ izquierda")
        velocidad = 2.0
        ang_z = 0
        giro = False

        ##self.robot.step(self.robotTimestep)        
        obstaculo, min = self.getObstaculoAIzquierda(350)
        fls = self.frontRightSensor.getValue()

        if((obstaculo==None or min>=self.minDistancia-0.12)and fls>=self.minDistancia-0.12):
            
            giro = True
            ant_gyroZ =self.giroscopio.getValues()[2]
            pasos=0

            while ((ang_z<(angulo))and(fls>=self.minDistancia-0.12)): #0.5*np.pi
                
                gyroZ =self.giroscopio.getValues()[2]
                ang_z=ang_z+(gyroZ*self.robotTimestep*0.001)
            
                self.ruedaDerechaSuperior.setVelocity(velocidad)
                self.ruedaDerechaInferior.setVelocity(velocidad)
                self.ruedaIzquierdaInferior.setVelocity(0.0)
                self.ruedaIzquierdaSuperior.setVelocity(0.0)
                self.updateTimestep()
                fls = self.frontRightSensor.getValue()

                if(gyroZ==ant_gyroZ):
                    pasos+=1
                    
                if(pasos == self.pasos):
                    giro=False
                    break;
                ant_gyroZ = gyroZ

        #self.detener()

        
        

        return giro
    
    def detener(self):
        """
            Permite detener al robot completamente poniendo a cero la velocidad de los motores.
            Luego de detenerse actualiza la señal.
        """

        #self.robot.step(self.robotTimestep) 
        
        self.ruedaDerechaSuperior.setVelocity(0)
        self.ruedaDerechaInferior.setVelocity(0)
        self.ruedaIzquierdaInferior.setVelocity(0)
        self.ruedaIzquierdaSuperior.setVelocity(0)

        self.updateTimestep()

        self.anteriorValorPositionSensor[0] = self.frontLeftPositionSensor.getValue()
        self.anteriorValorPositionSensor[1] = self.frontRightPositionSensor.getValue()
        self.anteriorValorPositionSensor[2] = self.rearLeftPositionSensor.getValue()
        self.anteriorValorPositionSensor[3] = self.rearRightPositionSensor.getValue()

        self.actualizarSenial();
#----------

#-----Acciones secundarias-----

    def avanzarObstaculo(self):
        """
            Determina la distancia al obstaculo frente al robot (utilizando el LIDAR) y avanza hasta el mismo.

            Retorna True si el robot pudo avanzar y False en caso contrario.
        """
        #self.robot.step(self.robotTimestep)
        obstaculo=self.getObstaculoAlFrente(4)

        distancia = self.distAvanceMax;
        velocidad = self.speedMax
        
        avance = False

        if (obstaculo!=None):
            distancia=obstaculo[2]
            #print(distancia)
        
        avance = self.avanzar(distancia-self.minDistancia, velocidad)

        return avance

    def avanzarSenial(self):
        """
            Avanza solamente si detecta una señal de radio. En cuyo caso se movera los metros equivalentes a la distancia que hay entre el robot y el emisor.

            Retorna True si el robot pudo avanzar y False en caso contrario.
        """
        #self.robot.step(self.robotTimestep)
        self.updateTimestep()
        avance = False

        if (self.haySenial()):
            distancia = self.distanciaSenial()
            #print(distancia)
            velocidad = self.speedMax
            avance = self.avanzar(distancia, velocidad)
        
        return avance

    def avanzarUltimaSenial(self):
        """
            Avanza la distancia almacenada en el atributo 'UltimaSenial'. En el caso que sea 'None' no se moverá.

            Retorna True si el robot pudo avanzar y False en caso contrario. 
        """
        #self.robot.step(self.robotTimestep)

        avance = False

        if (self.get_ultimaSenial()!=None):
            distancia = self.get_distanciaUltimaSenial()
            velocidad = self.speed
            
            avance = self.avanzar(distancia, velocidad)
        

        return avance

    def avanzarParaleloObstaculo(self):
        """
            Avanza paralelo al obstaculo en la orientación indicada.

            Args:
                obstaculo (integer): [1: Obstaculo a la izquierda. 2/otro: Obstaculo a la derecha]
            
            Return:
                Si avanzo un metro o más retorna True
        """
        index, distanciaDer = self.getObstaculoADerecha(40, 0.5)
        index, distanciaIzq = self.getObstaculoAIzquierda(360,0.5)

        recorrido = 0
        dist = [0, 0]
        recorrido = self.metrosRecorridos()
        p = 0
        plus_vel = 0
        ang_z=0

        if(distanciaDer<distanciaIzq):
            index, distanciaDer = self.getObstaculoADerecha(10, 1)
            
            while((index!=None)and(dist[0]<self.distAvanceMax+4 and dist[1]<self.distAvanceMax+4)
                    and(p<self.pasos)and(ang_z<(np.pi*0.5))and(self.getObstaculoAlFrente(0.05)==None)):
                #self.robot.step(self.robotTimestep)

                dist =  self.metrosRecorridos()
                gyroZ =self.giroscopio.getValues()[2]
                ang_z=ang_z+(gyroZ*self.robotTimestep*0.001)

                self.ruedaDerechaSuperior.setVelocity(self.speedMax+plus_vel)
                self.ruedaDerechaInferior.setVelocity(self.speedMax+plus_vel)
                self.ruedaIzquierdaInferior.setVelocity(self.speedMax-plus_vel)
                self.ruedaIzquierdaSuperior.setVelocity(self.speedMax-plus_vel)

                self.updateTimestep()
                if(dist==recorrido):
                    p+=1
                if((p == self.pasos)or(self.estimuloEncontrado(0.5))):
                    break;
                
                recorrido = dist
                index, distanciaDer = self.getObstaculoADerecha(10, 0.5)

                if((self.getObstaculoAlFrente(0.4)!=None)):
                    plus_vel+=0.5
                else:
                    plus_vel = 0

        else:
            index, distanciaIzq = self.getObstaculoAIzquierda(390,1)
            while((index!=None)and(dist[0]<self.distAvanceMax+4 and dist[1]<self.distAvanceMax+4)
                    and(p<self.pasos)and(ang_z<(np.pi*0.5))and(self.getObstaculoAlFrente(0.05)==None)):
                #self.robot.step(self.robotTimestep)

                dist =  self.metrosRecorridos()
                gyroZ =self.giroscopio.getValues()[2]
                ang_z=ang_z+(gyroZ*self.robotTimestep*0.001)

                self.ruedaDerechaSuperior.setVelocity(self.speedMax-plus_vel)
                self.ruedaDerechaInferior.setVelocity(self.speedMax-plus_vel)
                self.ruedaIzquierdaInferior.setVelocity(self.speedMax+plus_vel)
                self.ruedaIzquierdaSuperior.setVelocity(self.speedMax+plus_vel)

                self.updateTimestep()
                if(dist==recorrido):
                    p+=1

                if((p == self.pasos)or(self.estimuloEncontrado(0.5))):
                    break;
                
                recorrido = dist
                index, distanciaIzq = self.getObstaculoAIzquierda(390,0.5) 
                
                if((self.getObstaculoAlFrente(0.4)!=None)):
                    plus_vel+=0.5
                else:
                    plus_vel = 0

        #self.detener()
        #print("pasos: ",p < self.pasos," recorrido:",recorrido," ang_z:",ang_z<(np.pi*0.5)," index:",index)
        return ((recorrido[0]>0) or (recorrido[1]>0))

    def retrocederObstaculo(self):
        """
            Determina la distancia al obstaculo trasero al robot (utilizando el LIDAR) y retrocede hasta el mismo.

            Retorna True si el robot pudo retroceder y False en caso contrario.
        """
        #self.robot.step(self.robotTimestep)
        obstaculo=self.getObstaculoAtras(4)

        distancia = self.distAvanceMax;
        velocidad = self.speedMax
        
        retroceso = False

        if (obstaculo!=None):
            distancia=obstaculo[2]
            
        
        retroceso = self.retroceder(distancia, velocidad)
        return retroceso

    def giroParaleloObstaculo(self, pasos=0):
        """
            En el caso de que se detecte un obstaculo por el frente del robot, se procedera a girar paralelamente
            al mismo.

            Retorna True si se concreto el giro, y False en caso contrario.
        """
        giro = False
        #self.robot.step(self.robotTimestep)
        ##
        #print("Giro paraleo obstaculo. Pasos:",pasos)
        obstaculo = self.getObstaculoAlFrente(0.2)
        if((obstaculo==None)and((self.get_frontLeftSensor()<self.minDistancia)or(self.get_frontRightSensor()<self.minDistancia))):
            self.retroceder(0.1,2.0)
            #self.robot.step(self.robotTimestep)
            obstaculo = self.getObstaculoAlFrente(0.2)

        if(obstaculo!= None):
            if(obstaculo[0]==0):
                giro= self.giroIzquierda(0.5*np.pi)

            elif(obstaculo[1]=="right"):
                obst, min = self.getObstaculoAIzquierda(350)
                fls = self.frontLeftSensor.getValue()
                cond = ((obst==None or min>=self.minDistancia-0.12) and (fls>=self.minDistancia-0.12))

                if(cond):
                    giro= self.giroIzquierdaParaleloObstaculo()
                
                if((not cond) or (not giro)):
                    self.retroceder(0.1,2.0)
                    giro = self.giroDerechaParaleloObstaculo()
            else: 
                obst, min= self.getObstaculoADerecha(40)
                frs = self.frontRightSensor.getValue()
                cond = ((obst==None or min>=self.minDistancia-0.12) and (frs>=self.minDistancia-0.12))

                if(cond):
                    giro= self.giroDerechaParaleloObstaculo()

                if((not cond) or (not giro)):
                    self.retroceder(0.1,2.0)
                    giro = self.giroIzquierdaParaleloObstaculo()
                   
        return giro
            
    def giroParaleloObstaculoGuiado(self):
        """
            En el caso de que se detecte un obstaculo por el frente del robot, se procedera a girar paralelamente
            al mismo en direccion a la ultima señal encontrada.

            Retorna True si se concreto el giro, y False en caso contrario.
        """
        #print("Giro paraleo obstaculo guiado")
        obstaculo = self.getObstaculoAlFrente(0.2)
        if((obstaculo==None)and((self.get_frontLeftSensor()<self.minDistancia)or(self.get_frontRightSensor()<self.minDistancia))):
            self.retroceder(0.1,2.0)
            #self.robot.step(self.robotTimestep)
            obstaculo = self.getObstaculoAlFrente(0.2)

        giro = False
            
        if(obstaculo!= None):
            self.updateTimestep()
            pared_izq, long_izq = self.detectarParedIzquierda(1)
            pared_der, long_der = self.detectarParedDerecha(1)
            print("izq:",pared_izq," long:",long_izq)
            print("der:",pared_der," long:",long_der)
            # Comparar longitudes para decidir hacia qué lado girar
            if pared_izq or pared_der:
                if (not pared_izq)or(long_izq+1 < long_der):
                    print(long_izq+1 ,"<", long_der)
                    giro = self.giroIzquierdaParaleloObstaculo()
                elif(not pared_der)or(long_der+1  < long_izq):
                    print(long_der+1 ,"<", long_izq)
                    giro = self.giroDerechaParaleloObstaculo()   

            direccion = self.orientacionUltimaSenial()    
            
            if ((direccion==1)and(not giro)):
                if(obstaculo[2]<self.minDistancia-0.2):
                    self.retroceder(0.1,2)
                giro = self.giroIzquierdaParaleloObstaculo()
            
            elif((direccion == 2)and(not giro)):
                if(obstaculo[2]<self.minDistancia-0.2):
                    self.retroceder(0.1,2)
                giro = self.giroDerechaParaleloObstaculo()
            
        return giro

    def giroIzquierdaParaleloObstaculo(self):
        #self.robot.step(self.robotTimestep)
        ##
        #print("giro a izquierda Paralelo Obsts")
        obstaculo = False
        finalizo=False

        indice, min= self.getObstaculoAIzquierda(335)
        obstaculoLidar = self.getObstaculoAlFrente(0.2)
        #print(indice," - min:",min)
        if(obstaculoLidar!=None):
            obstaculo = obstaculoLidar[2]<self.minDistancia+0.2
        else:
            fls = self.get_frontLeftSensor()
            frs = self.get_frontRightSensor()
            obstaculo = ((fls<self.minDistancia+0.2)or(frs<self.minDistancia+0.2))
       
        if(((indice == None)or(indice!=None and min>0.25))and(obstaculo)):
            #self.robot.step(self.robotTimestep)
            ang_z=0
            ant_gyroZ =self.giroscopio.getValues()[2]
            pasos=0
            while(obstaculo):
                gyroZ =self.giroscopio.getValues()[2]
                ang_z=ang_z+(gyroZ*self.robotTimestep*0.001)

                self.ruedaDerechaSuperior.setVelocity(2)
                self.ruedaDerechaInferior.setVelocity(2)
                self.ruedaIzquierdaInferior.setVelocity(-1.5)
                self.ruedaIzquierdaSuperior.setVelocity(-1.5)

                #self.robot.step(self.robotTimestep)
                self.updateTimestep()
                obstaculoLidar = self.getObstaculoAlFrente(0.3)
                fls = self.get_frontLeftSensor()
                frs = self.get_frontRightSensor()
                obstaculo = (obstaculoLidar!=None)or(((fls<self.minDistancia+0.2)or(frs<self.minDistancia+0.2)))
                
                if(gyroZ==ant_gyroZ):
                    pasos+=1
                if(pasos == self.pasos):
                    finalizo=False
                    break;
                ant_gyroZ = gyroZ
                finalizo=True

            #self.detener()

        return finalizo
    
    def giroDerechaParaleloObstaculo(self):
        """
            Utiliza el lidar para detectar el obstaculo más cercano del lado izquierdo del robot y gira hasta 
            ponerse paralelo al mismo.

            Retorna True si se concreto el giro, y False en caso contrario.
        """
        #self.robot.step(self.robotTimestep)
        ##
        obstaculo = False
        finalizo=False
        indice, min= self.getObstaculoADerecha(64, 0.2)
        #print(indice," ",min)
        
        #self.robot.step(self.robotTimestep)

        obstaculoLidar = self.getObstaculoAlFrente(0.2)
        if(obstaculoLidar!=None):
            obstaculo = obstaculoLidar[2]<self.minDistancia+0.2
        else:
            fls = self.get_frontLeftSensor()
            frs = self.get_frontRightSensor()
            obstaculo = ((fls<self.minDistancia+0.2)or(frs<self.minDistancia+0.2))
            
        
        if(((indice== None)or(indice!=None and min>0.25))and(obstaculo)):
            #self.robot.step(self.robotTimestep)
            ant_gyroZ =self.giroscopio.getValues()[2]
            ang_z=0
            pasos=0
            while(obstaculo):
                gyroZ =self.giroscopio.getValues()[2]
                ang_z=ang_z+(gyroZ*self.robotTimestep*0.001)

                self.ruedaDerechaSuperior.setVelocity(-1.5)
                self.ruedaDerechaInferior.setVelocity(-1.5)
                self.ruedaIzquierdaInferior.setVelocity(2)
                self.ruedaIzquierdaSuperior.setVelocity(2)

                #self.robot.step(self.robotTimestep)
                self.updateTimestep()
                obstaculoLidar = self.getObstaculoAlFrente(0.3)
                fls = self.get_frontLeftSensor()
                frs = self.get_frontRightSensor()
                obstaculo = (obstaculoLidar!=None)or(((fls<self.minDistancia+0.2)or(frs<self.minDistancia+0.2)))
                
                if(gyroZ==ant_gyroZ):
                    pasos+=1
                if(pasos == self.pasos):
                    finalizo=False
                    break;
                ant_gyroZ = gyroZ
                finalizo=True

            #self.detener()
            
        return finalizo

    def giroAleatorioIzquierda(self):
        """
            Determina de forma aleatorea y uniforme un angulo de giro entre 10 y 25 grados, para posteriormente girar
            hacia la izquierda dicho valor.

            Retorna True si se concreto el giro, y False en caso contrario.
        """
        angulo = np.random.uniform(low=0.174533, high=0.125*np.pi)
        #self.robot.step(self.robotTimestep)
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
        #self.robot.step(self.robotTimestep)
        
        giro = False
        giro = self.giroDerecha(angulo)
        return giro

    def giroSenial(self):
        """
            Busca una señal emitida y gira el robot hacia ella.

            Retorna True si se concreto el giro y False en caso contrario.
        """
        #self.robot.step(self.robotTimestep)
        #self.updateTimestep()
        giro = False
        
        if (self.haySenial()):
            self.retroceder(0.01,2.0)
            angulo=0
            direccion = self.orientacionUltimaSenial()    
            if (direccion==1):
                #self.robot.step(self.robotTimestep)
                obstaculo, min = self.getObstaculoAIzquierda(360)
                if(obstaculo==None):
                    angulo = self.anguloUltimaSenial()/2
                    giro = self.giroIzquierda(angulo)
                    giro = self.giroIzquierda(angulo) #no esta repetida
            else:
                #self.robot.step(self.robotTimestep)
                obstaculo, min = self.getObstaculoADerecha(40)
                if(obstaculo==None):
                    angulo = self.anguloUltimaSenial()
                    giro = self.giroDerecha(angulo)

            if(angulo<=(np.pi*(1/12))):
                return True
            else:
                return giro
        else:
            return giro
    
#----------

#----Funciones sensoriales------


#-----Giroscopio-----
    def get_giroscopio(self):
        """
        Retorna el valor del giroscopio.
        """
        return self.giroscopio.getValues()
    
    def get_orientacion_robot(self):
        """
        Obtiene la orientación actual del robot usando el giroscopio.
        Retorna el ángulo en radianes.
        """
        gyro_values = self.giroscopio.getValues()
        # El giroscopio da velocidad angular, necesitas integrar para obtener orientación
        # O usar el acelerómetro para obtener orientación absoluta
        accel_values = self.acelerometro.getValues()
        
        # Calcular orientación usando acelerómetro (más estable para orientación absoluta)
        orientacion = math.atan2(accel_values[1], accel_values[0])
        return orientacion
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

#----Ubicación y Rotación------

    def currentLocation(self):
        """
            Retorna la ubicación exácta del agente dentro del simulador.
        """
        return self.translation.getSFVec3f()

#-----

    def currentRotation(self):
        """
            Retorna la rotación exácta del agente dentro del simulador.
        """
        return self.rotation.getSFRotation()
    
#---------------

#-----Default-----
    def default(self):
        """
        Inicializa los valores de los sensores de posición a cero.
        """
        self.distanciaRecorrida = 0
        self.direccionUltimaSenial = None
        self.distanciaUltimaSenial = None
        self.ant_dist_senial = None
        self.ant_angulo = None
        
        self.detener()
        self.defaultPositionSensorAnterior()
        
        
#-----Valor anterior de sensor de posicion-----
    def get_anteriorValorPositionSensor(self):
        return self.anteriorValorPositionSensor

    def defaultPositionSensorAnterior(self):
        self.anteriorValorPositionSensor = [0,0,0,0]
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
        
        for i in range(2):
            distancia[i] = ps_values[i]*self.encoderUnit

        ##print("metros recorridos: {} {}".format(distancia[0], distancia[1]))
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
        ##print("position values: {} {}".format(ps_values[0],ps_values[1]))
        for i in range(2):
            distancia[i] = ps_values[i]*self.encoderUnit

        ##print("metros recorridos: {} {}".format(distancia[0], distancia[1]))

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
        return self.receptor.getQueueLength()
    
    def getSignalStrength(self):
        """ 
        Retorna la fuerza de la señal.
        """
        return self.receptor.getSignalStrength()
    
    def getEmitterDirection(self):
        """ 
        Retorna un vector normalizado(length=1) que indica la dirección del emisor con respecto al receptor.
        """
        punteroDireccion = self.receptor.getEmitterDirection()
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
        self.activateRobotTimestep()
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
        self.updateTimestep()
        #self.robot.step(self.robotTimestep)
        
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
        self.set_distanciaUltimaSenial(None)

    def actualizarSenial(self):
        """
        Actualiza el atributo 'ultimaSenial' y 'distanciaUltimaSenial'almacenando la dirección y la distancia ultima señal encontrada respectivamente.
        """
        #self.robot.step(self.robotTimestep)
        self.updateTimestep()
        if(self.haySenial()):
            self.set_ultimaSenial(self.getEmitterDirection()) 
            self.set_distanciaUltimaSenial(self.distanciaSenial())

        self.vaciarCola();

    def vaciarCola(self):
        """
        Vacia la cola del receiver que contiene todos los paquetes recibidos hasta el momento.
        """
        while(self.get_receiver() > 0):
            self.receptor.nextPacket()

    def orientacionUltimaSenial(self):
        """
            Retorna la orientacion de la ultima señal almacenada.

            Retorno: 
                1 : señal a la izquierda.
                2 : señal a la derecha.
                3 : orientacio desconocida.
            
        """
        #self.robot.step(self.robotTimestep)
        self.updateTimestep()
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
        if(direccion == None):
            return None
        else:
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
        #self.robot.step(self.robotTimestep)
        lidar_data = self.lidar.getRangeImage()
        fr = self.front_range # 20
        lidar_front = lidar_data[:fr] + lidar_data[-fr:]        # mitad primera: r, mitad izq: l
        ##print(lidar_front)
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
        #self.robot.step(self.robotTimestep)
        lidar_data = self.lidar.getRangeImage()
        br = self.back_range # 25
        lidar_back = lidar_data[200-br:200+br]        # mitad primera: r, mitad izq: l
        ##print(lidar_front)
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
        
        La derecha del lidar se define desde el punto recibido por parametro hasta el punto 124 que indica poco mas de 90º
        
        Args:
            punto_inicio (integer): [Punto de inicio en el que el lidar será leido]
            extra (float): [Distancia extra a la mínima al obstaculo, por defecto cero].
        """
        #self.robot.step(self.robotTimestep)
        er = self.error_range
        lidar_data = self.lidar.getRangeImage()
        lidar_right = lidar_data[punto_inicio : 99+self.front_range]
        obstaculo, min = self.getObstaculo(lidar_right,extra)
        return obstaculo, min

    def getObstaculoAIzquierda(self, punto_fin, extra=0):
        """
        Retorna el punto en el que se encuentra la menor distancia al obstaculo sobre la izquierda del lidar.
        
        La izquierda del lidar se define desde el punto 275 (menos de 180º) hasta el punto pasado por parametro.
        
        Args:
            punto_fin (integer): [Punto final en el que el lidar será leido]
            extra (float): [Distancia extra a la mínima al obstaculo, por defecto cero punto].
        """
        #self.robot.step(self.robotTimestep)
        er = self.error_range
        lidar_data = self.lidar.getRangeImage()
        lidar_left = lidar_data[300-self.front_range:punto_fin]
        obstaculo, min = self.getObstaculo(lidar_left,extra)
        return obstaculo, min

    def detectarParedDerecha(self, distancia_max=2.0, tolerancia_continuidad=0.1):
        """
        Detecta si hay una pared a la izquierda del robot y calcula su longitud.
        
        Args:
            distancia_max (float): Distancia máxima para considerar que hay una pared (metros)
            tolerancia_continuidad (float): Tolerancia para considerar puntos como continuos (metros)
            
        Returns:
            tuple: (hay_pared, longitud_pared)
                - hay_pared (bool): True si se detecta una pared, False en caso contrario
                - longitud_pared (float): Longitud estimada de la pared en metros
        """
        # Obtener datos del lidar
        lidar_data = np.array(self.lidar.getRangeImage())
        
        lidar_data[np.isinf(lidar_data)] = 2
        
        # Rango de ángulos para el lado izquierdo (aproximadamente 90 grados a la izquierda)
        # Considerando que el lidar tiene 400 puntos y el punto 0 es el frente
        # El lado izquierdo corresponde aproximadamente a los puntos 75-125 (90° ± 22.5°)
        inicio_izquierda = 75
        fin_izquierda = 125
        
        puntos_pared = []
        hay_pared = False
        
        # Analizar los puntos del lado izquierdo
        for i in range(inicio_izquierda, fin_izquierda + 1):
            if i < len(lidar_data):
                distancia = lidar_data[i]
                
                # Verificar si el punto está dentro del rango de detección
                if distancia <= distancia_max and distancia > 0.05:  # 0.05m mínimo para evitar ruido
                    # Calcular la posición del punto en coordenadas cartesianas
                    angulo = (i / len(lidar_data)) * 2 * np.pi
                    x = distancia * np.cos(angulo)
                    y = distancia * np.sin(angulo)
                    puntos_pared.append((x, y, distancia))
        
        # Si hay suficientes puntos, verificar continuidad para determinar si es una pared
        if len(puntos_pared) >= 3:
            puntos_continuos = []
            secuencia_actual = [puntos_pared[0]]
            
            for i in range(1, len(puntos_pared)):
                # Calcular distancia entre puntos consecutivos
                x1, y1, d1 = puntos_pared[i-1]
                x2, y2, d2 = puntos_pared[i]
                distancia_puntos = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                
                # Si los puntos están dentro de la tolerancia de continuidad
                if distancia_puntos <= tolerancia_continuidad:
                    secuencia_actual.append(puntos_pared[i])
                else:
                    # Guardar la secuencia actual si es suficientemente larga
                    if len(secuencia_actual) >= 3:
                        puntos_continuos.extend(secuencia_actual)
                    secuencia_actual = [puntos_pared[i]]
            
            # Agregar la última secuencia
            if len(secuencia_actual) >= 3:
                puntos_continuos.extend(secuencia_actual)
            
            # Si hay suficientes puntos continuos, considerar que hay una pared
            if len(puntos_continuos) >= 3:
                hay_pared = True
                
                # Calcular longitud de la pared
                if len(puntos_continuos) >= 2:
                    x_min = min(punto[0] for punto in puntos_continuos)
                    x_max = max(punto[0] for punto in puntos_continuos)
                    y_min = min(punto[1] for punto in puntos_continuos)
                    y_max = max(punto[1] for punto in puntos_continuos)
                    
                    longitud_pared = np.sqrt((x_max-x_min)**2 + (y_max-y_min)**2)
                else:
                    longitud_pared = 0.0
            else:
                longitud_pared = 0.0
        else:
            longitud_pared = 0.0
        
        return hay_pared, longitud_pared

    def detectarParedIzquierda(self, distancia_max=2.0, tolerancia_continuidad=0.1):
        """
        Detecta si hay una pared a la derecha del robot y calcula su longitud.
        
        Args:
            distancia_max (float): Distancia máxima para considerar que hay una pared (metros)
            tolerancia_continuidad (float): Tolerancia para considerar puntos como continuos (metros)
            
        Returns:
            tuple: (hay_pared, longitud_pared)
                - hay_pared (bool): True si se detecta una pared, False en caso contrario
                - longitud_pared (float): Longitud estimada de la pared en metros
        """
        # Obtener datos del lidar
        lidar_data = np.array(self.lidar.getRangeImage())
        
        lidar_data[np.isinf(lidar_data)] = 2
        # Rango de ángulos para el lado derecho (aproximadamente 90 grados a la derecha)
        # Considerando que el lidar tiene 400 puntos y el punto 0 es el frente
        # El lado derecho corresponde aproximadamente a los puntos 275-325 (270° ± 22.5°)
        inicio_derecha = 275
        fin_derecha = 325
        
        puntos_pared = []
        hay_pared = False
        
        # Analizar los puntos del lado derecho
        for i in range(inicio_derecha, fin_derecha + 1):
            if i < len(lidar_data):
                distancia = lidar_data[i]
                
                # Verificar si el punto está dentro del rango de detección
                if distancia <= distancia_max and distancia > 0.05:  # 0.05m mínimo para evitar ruido
                    # Calcular la posición del punto en coordenadas cartesianas
                    angulo = (i / len(lidar_data)) * 2 * np.pi
                    x = distancia * np.cos(angulo)
                    y = distancia * np.sin(angulo)
                    puntos_pared.append((x, y, distancia))
        
        # Si hay suficientes puntos, verificar continuidad para determinar si es una pared
        if len(puntos_pared) >= 3:
            puntos_continuos = []
            secuencia_actual = [puntos_pared[0]]
            
            for i in range(1, len(puntos_pared)):
                # Calcular distancia entre puntos consecutivos
                x1, y1, d1 = puntos_pared[i-1]
                x2, y2, d2 = puntos_pared[i]
                distancia_puntos = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                
                # Si los puntos están dentro de la tolerancia de continuidad
                if distancia_puntos <= tolerancia_continuidad:
                    secuencia_actual.append(puntos_pared[i])
                else:
                    # Guardar la secuencia actual si es suficientemente larga
                    if len(secuencia_actual) >= 3:
                        puntos_continuos.extend(secuencia_actual)
                    secuencia_actual = [puntos_pared[i]]
            
            # Agregar la última secuencia
            if len(secuencia_actual) >= 3:
                puntos_continuos.extend(secuencia_actual)
            
            # Si hay suficientes puntos continuos, considerar que hay una pared
            if len(puntos_continuos) >= 3:
                hay_pared = True
                
                # Calcular longitud de la pared
                if len(puntos_continuos) >= 2:
                    x_min = min(punto[0] for punto in puntos_continuos)
                    x_max = max(punto[0] for punto in puntos_continuos)
                    y_min = min(punto[1] for punto in puntos_continuos)
                    y_max = max(punto[1] for punto in puntos_continuos)
                    
                    longitud_pared = np.sqrt((x_max-x_min)**2 + (y_max-y_min)**2)
                else:
                    longitud_pared = 0.0
            else:
                longitud_pared = 0.0
        else:
            longitud_pared = 0.0
        
        return hay_pared, longitud_pared
    
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

#----- Actualizar paso ----
    def updateTimestep(self):
        """
        Actualiza el tiempo de paso del robot.
        
        Returns:
            int: El tiempo de paso del robot.
        """
        super(Supervisor, self).step(self.robotTimestep)

    def activateRobotTimestep(self):
        """_summary_
        """
        for i in range(0,2):
            self.updateTimestep()

#----- Atributos de la clase----
    def getRobotTimestep(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self.robotTimestep
    
#--------------------