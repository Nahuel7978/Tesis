"""my_controller_rosbot controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot, Motor, Receiver, Supervisor
from Movimientos.HROSbot import * 
from Comportamientos.BehavioralHROSbot import * 
from Qlearning.AdaptiveHROSbot import * 
from Qlearning.ActionAdaptativeHROSbot import * 
from Qlearning.BehavioralAdaptativeHROSbot import * 
from Training.ActionTraining import *
from Training.BehavioralTraining import *

import numpy as np
import math
import time

# create the Robot instance.

robot = Robot()
# get the time step of the current world. 
timestep = int(robot.getBasicTimeStep()) # timestep = 32 

rosbot = BehavioralAdaptativeHROSbot(robot,0.1,0.7,0.2)
rosbot_action = ActionAdaptativeHROSbot(robot,0.1,0.7,0.2)

entorno = BehavioralTraining(5,2,1,-5,50,20)
entorno_acciones = ActionTraining(5,3,1,-1,-3,-5,50,35)

rosbotComp = BehavioralHROSbot(robot)
llegue = False

time.sleep(1)
for i in range(10):  # Ignorar los primeros 5 pasos del simulador
    robot.step(timestep)

#
#rosbot.avanzarObstaculo()
#rosbot.retrocederObstaculo()
#rosbot.avanzarUltimaSenial()
#rosbot.giroParaleloObstaculo()

#rosbot.giroParaleloObstaculoGuiado()
#rosbot.giroIzquierdaParaleloObstaculo()
#rosbot.giroIzquierdaParaleloObstaculo()
#rosbot.giroDerechaParaleloObstaculo()
#rosbot.giroIzquierdaParaleloObstaculo()
#rosbot.giroAleatorioIzquierda()
#rosbot.giroAleatorioDerecha()
#rosbot.avanzar(1,8)
#rosbot.giroSenial()
#rosbot.avanzarUltimaSenial()
#rosbot.avanzarUltimaSenial()
#rosbot.visualizarPoliticas()

#rosbot.ir_estimulo()
#rosbot.evitarObstaculo()

#rosbot.evitarObstaculo()
#rosbot.ir_estimulo()


#rosbot_action.avanzar(1,8)
#rosbot_action.giroAleatorioDerecha()
#rosbot_action.giroAleatorioIzquierda()
#rosbot_action.retroceder(1,3)
#rosbot_action.retroceder(1,3)
#rosbot_action.giroParaleloObstaculo()
#rosbot_action.giroAleatorioDerecha()
#rosbot.avanzarParaleloObstaculo()

#ACTION ADAPTATIVE
#rosbot_action.cargarPoliticas()
#entorno_acciones.entrenamiento(rosbot_action)    
#entorno_acciones.visualizarRegistroEntrenamiento()
#rosbot_action.cargarPoliticas()
#rosbot_action.visualizarPoliticas()


"""
print("--------------")
print("MODELO ENTRENADO")
print("--------------")
i=1
acc = 0
while((robot.step(timestep) != -1)and(not llegue)):
    print("--->Accion",i,"<---")
    i+=1
    rosbot_action.estadoActual(acc)
    acc = rosbot_action.vivir(acc)

    llegue =  rosbot_action.estimuloEncontrado(0.3)
    
    print("--------------")

"""
#""" 
#BEHAVIOR ADAPTATIVE
#rosbot.cargarPoliticas()
#rosbot.visualizarPoliticas()

    # Entrenamiento del entorno
entorno.entrenamiento(rosbot)    

    
#entorno.visualizarRegistroEntrenamiento()
#rosbot.visualizarPoliticas()
"""
print("--------------")
print("MODELO ENTRENADO")
print("--------------")
i=1
acc = 0
while((robot.step(timestep) != -1)and(not llegue)):
    print("--->Comportamiento",i,"<---")
    i+=1
    acc =    rosbot.vivir(acc)
    llegue =  rosbot.estimuloEncontrado(0.3)
    print("--------------")
    
#rosbot.displayMapa()
#"""

"""
#Braitenberg
print("--------------")
print("MODELO BRAINTENBERG")
print("--------------")
i=1
evitar = False
ir = False
explorar = False
while(robot.step(timestep) != -1)and(not llegue):
    print("------Comportamiento ",i,"----------")
    i+=1
    evitar = False
    ir = False
    explorar = False
    
    if(rosbotComp.getObstaculoAlFrente() != None):
        print("Evitar Obstaculo")
        evitar = rosbotComp.evitarObstaculo()
    if((rosbotComp.get_receiver() > 0)and(not evitar)):
        print("Ir Estimulo")
        ir = rosbotComp.ir_estimulo()
    if((not ir) and (not evitar)):
        print("Explorar")
        explorar = rosbotComp.explorar()
        
    llegue =  rosbotComp.estimuloEncontrado(0.4)
        
#rosbotComp.displayMapa()
"""