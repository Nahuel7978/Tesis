
# 🤖 Simulation Control App

### Plataforma cliente-servidor para entrenamiento remoto de agentes inteligentes en Webots

---

## Descripción general

**Simulation Control App** es una plataforma cliente-servidor diseñada para ejecutar entrenamientos de *Reinforcement Learning* (RL) en el simulador **Webots** de manera remota, eficiente y reproducible.
El sistema busca reducir los costos computacionales y la complejidad técnica que implica entrenar agentes inteligentes localmente, permitiendo delegar el entrenamiento a un backend automatizado que gestiona contenedores aislados y reporta el progreso en tiempo real.

El proyecto se compone de tres partes principales:

1. **Usuario / Entorno local:**
   El usuario implementa su propio *controlador de agente* basado en **DeepBots**, **Stable-Baselines3** y **OpenAI Gym**.
   Dicho controlador debe extender la clase `RobotSupervisorEnv` (de DeepBots), y luego enviarse junto al mundo de simulación comprimido (`.zip`) al servidor.

2. **Backend / API REST y WebSocket:**
   La API —desarrollada en **Python (FastAPI)**— recibe los paquetes de simulación, los algoritmos de entrenamiento y los hiperparámetros.
   Al recibir una solicitud, genera un *job* y levanta un contenedor **Docker** aislado que ejecuta el entrenamiento en modo *headless* (sin renderizado).
   Durante el entrenamiento, las métricas se transmiten en tiempo real mediante **WebSockets**, permitiendo el monitoreo continuo desde la interfaz.

3. **Frontend / Aplicación de escritorio:**
   Aplicación desarrollada en **React + Tauri**, multiplataforma y liviana, que funciona como interfaz gráfica del sistema.
   Permite enviar nuevos *jobs*, visualizar su estado (pendiente, en ejecución o completado), monitorear métricas de aprendizaje y descargar los modelos entrenados.

---

## 🎯 Objetivo del proyecto

Desarrollar una infraestructura escalable y multiplataforma que facilite el entrenamiento remoto de agentes inteligentes en Webots, integrando una arquitectura cliente-servidor basada en contenedores, una API REST, y una aplicación de escritorio moderna e intuitiva para la gestión y monitoreo de experimentos.

---

## Componentes principales

### 🧩 Backend (API Server)

* Desarrollado con **FastAPI** y **Python 3.10**.
* Expone endpoints REST para:

  * Subir mundos
  * Configurar algoritmos y parámetros
  * Iniciar y detener entrenamientos
  * Consultar estado de *jobs*
* Comunicación **WebSocket** para:

  * Emitir métricas en tiempo real (reward, loss, episodios, pasos, etc.)
  * Notificar cambios de estado (*running*, *completed*, *error*)
* Uso de **Docker SDK** para gestionar contenedores dinámicos.
* Configuración flexible a través de archivos JSON

### 💻 Frontend (Interfaz de usuario)

* Construido con **React** y ejecutado en **Tauri** para garantizar bajo consumo de recursos.
* Permite:

  * Visualizar *jobs* en un panel principal (estado, progreso, tiempo, resultados).
  * Acceder a una vista detallada con gráficos de métricas y botones de descarga.
  * Crear nuevos *jobs* seleccionando:

    * Mundo de simulación `.zip`
    * Algoritmo (PPO, DQN, A2C, etc.)
    * Hiperparámetros (learning rate, batch size, discount factor, etc.)
  * Interactuar con la API vía HTTP y WebSocket.

### 🤖 Usuario / Controlador

* Define el comportamiento del agente y del entorno.
* Debe heredar de `RobotSupervisorEnv` (DeepBots).
* Puede ejecutar cualquier algoritmo compatible con Stable-Baselines3.
* Ejemplo de estructura esperada:

  ```python
  class MyRobotEnv(RobotSupervisorEnv):
      def get_observations(self):
          ...
      def get_reward(self):
          ...
      def is_done(self):
          ...
  ```

--- 
## Instalación y ejecución

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run tauri dev
```

---

## 🔮 Futuras mejoras

* Autenticación y lógica de usuario.
* Base de datos para registro histórico de entrenamientos.
* Ampliación a otros simuladores.
* Migración opcional a versión web completa (sin Tauri).

---

## 👤 Autor

**Nahuel Román**
Estudiante avanzado de Ingeniería en Sistemas | Enfocado en Inteligencia Artificial y Arquitecturas de Software
📧 [[roman.n7978@gmail.com](roman.n7978@gmail.com)]
🔗 [LinkedIn](https://www.linkedin.com/in/nahuel-rom%C3%A1n/) | [GitHub](https://github.com/Nahuel7978)

---

## 🇬🇧 English version

# 🤖 Simulation Control App

### Client-server platform for remote training of intelligent agents in Webots

---

### Overview

**Simulation Control App** is a client-server platform designed to run *Reinforcement Learning* (RL) training in the **Webots** simulator remotely and efficiently.
It offloads heavy computational tasks from the user’s machine by delegating training to an automated backend that manages Docker containers and streams metrics in real time.

The system consists of three main components:

1. **User / Local environment:**
   Users implement their custom agent controller using **DeepBots**, **Stable-Baselines3**, and **OpenAI Gym**, extending the `RobotSupervisorEnv` class, and then submit their simulation world as a `.zip` package.

2. **Backend (API + WebSocket):**
   Developed in **FastAPI (Python)**, the API receives the world file, algorithm, and hyperparameters, then spawns an isolated **Docker** container to execute the training in *headless mode*.
   Training metrics are streamed back to clients in real time through **WebSockets**.

3. **Frontend (Desktop App):**
   A lightweight, cross-platform interface built with **React + Tauri** that enables users to submit, monitor, and visualize training jobs and download trained models.

---

## 🎯 Project Objective

Develop a scalable, cross-platform infrastructure that facilitates remote training of intelligent agents in Webots, integrating a container-based client-server architecture, a REST API, and a modern and intuitive desktop application for managing and monitoring experiments.

---

## Core Components

### 🧩 Backend (API Server)

* Developed with **FastAPI** and **Python 3.10**.
* Exposes REST endpoints for:

* Uploading worlds
* Configuring algorithms and parameters
* Starting and stopping workouts
* Checking the status of *jobs*
* WebSocket communication for:

* Emitting real-time metrics (reward, loss, episodes, steps, etc.)
* Notifying of status changes (*running*, *completed*, *error*)
* Using the **Docker SDK** to manage dynamic containers.
* Flexible configuration via JSON files

### 💻 Frontend (User Interface)

* Built with **React** and running on **Tauri** to ensure low resource consumption.
* Allows you to:

* View jobs in a main dashboard (status, progress, time, results).
* Access a detailed view with metric charts and download buttons.
* Create new jobs by selecting:

* Simulation world `.zip`
* Algorithm (PPO, DQN, A2C, etc.)
* Hyperparameters (learning rate, batch size, discount factor, etc.)
* Interact with the API via HTTP and WebSocket.

### 🤖 User / Controller

* Defines the behavior of the agent and the environment.
* Must inherit from `RobotSupervisorEnv` (DeepBots).
* Can run any algorithm compatible with Stable-Baselines3.
* Example of expected structure:
  ```python
  class MyRobotEnv(RobotSupervisorEnv):
      def get_observations(self):
          ...
      def get_reward(self):
          ...
      def is_done(self):
          ...
  ```

---

## 🔮 Future improvements

* Authentication and user logic.
* Database for historical training records.
* Expansion to other simulators.
* Optional migration to a full web version (without Tauri).

---

## 👤 Author

**Nahuel Román**
Advanced Systems Engineering Student | Focused on Artificial Intelligence and Software Architecture
📧 [[roman.n7978@gmail.com](roman.n7978@gmail.com)]
🔗 [LinkedIn](https://www.linkedin.com/in/nahuel-rom%C3%A1n/) | [GitHub](https://github.com/Nahuel7978)
  
Would you like me to **add example requests (HTTP and WebSocket snippets)** to make the README more developer-friendly (for someone who wants to test or extend your API)?
Puedo incluir ejemplos de `curl`, `WebSocket` y estructura de JSON del `train_config.json` si querés dejarlo más técnico.
