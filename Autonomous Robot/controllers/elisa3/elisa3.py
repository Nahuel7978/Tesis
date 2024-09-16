from controller import Robot, Emitter
import struct
import time


robot = Robot()
timestep = int(robot.getBasicTimeStep())
emitter = robot.getDevice('Emitter')

while (robot.step(timestep) != -1):
    emitter.send(float(time.time()))