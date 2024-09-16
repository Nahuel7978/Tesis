
from Movimientos.HROSbot import *
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

class Mapa():

    def __init__(self, bot, nombre):
        self.nombre = nombre
        self.bot = bot
        self.obstacles = []
        self.map = []
        self.pi_x, self.pi_y = -1.0, -3.0
        self.x, self.y, self.theta = self.pi_x, self.pi_y, 0

    def update(self, latest_move):
        if latest_move['type'] == 'giro':
            self.theta += -latest_move['value']
        elif latest_move['type'] == 'avance':
            self.y += latest_move['value'] * np.cos(self.theta)
            self.x += latest_move['value'] * np.sin(self.theta)
        self.map.append([self.x,self.y])

    def display(self):
        fig, ax = plt.subplots()
        if self.map:
            trajectory_x, trajectory_y = zip(*self.map)
            plt.plot(trajectory_x, trajectory_y, marker='o')
        if self.obstacles:
            x_coords, y_coords = zip(*self.obstacles)
            plt.scatter(x_coords, y_coords, c='red', s=5)

        plt.title('Trayectoria del Robot')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.grid()

        # El tablero es de 8x8 metros
        dim = 7.5               # Recomiendo usar 7.5
        half_dim = dim/2
        offset = .15
        map_dim = half_dim+offset

        plt.xlim(-half_dim, half_dim)
        plt.ylim(-half_dim, half_dim)

        # Insertar imágen del entorno como fondo en el mapa
        current_dir = os.path.dirname(__file__)
        background_image_path = os.path.join(current_dir, 'images', 'backround.png')
        img = mpimg.imread(background_image_path)
        ax.imshow(img, extent=[-map_dim, map_dim, -map_dim, map_dim], alpha=0.5)

        # Asegurar que los ejes tengan la misma escala
        plt.gca().set_aspect('equal', adjustable='box')

        # Colocar el origen (0,0) en el centro
        plt.axhline(self.pi_y, color='black',linewidth=0.5)
        plt.axvline(self.pi_x, color='black',linewidth=0.5)
        plt.show()


class MapaNavegacion:

    def __init__(self, bot):
        self.bot = bot
        self.odometryMap = Mapa(bot, 'odometry map')

    def update(self, latest_move):
        self.odometryMap.update(latest_move)

    def display(self):
        self.odometryMap.display()
