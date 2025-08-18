import docker
import os
import threading
# Configuración
IMAGE_NAME = "webots_image"  # Nombre de tu imagen
WORLD_PATH = "/home/roman7978/Documentos/university_portfolio/Tesis/Autonomous Robot/worlds"  # Ruta absoluta en tu host
WORLD_NAME = "Autonomous Robot.wbt"
PROTOS_PATH = "/home/roman7978/Documentos/university_portfolio/Tesis/Autonomous Robot/protos"  # Ruta absoluta en tu host
CONTROLERS_PATH = "/home/roman7978/Documentos/university_portfolio/Tesis/Autonomous Robot/controllers"  # Ruta absoluta en tu host
CONTAINER_WORLD_PATH = "/workspace/worlds"  # Ruta donde lo verá el contenedor
CONTAINER_PROTOS_PATH = "/workspace/protos"  # Ruta donde están los protos en el contenedor
CONTAINER_CONTROLLERS_PATH = "/workspace/controllers"  # Ruta donde están los controladores en el contenedor

def run_webots_world(image_name, world_file, local_worlds_dir, local_protos, local_controllers, container_name="webots_headless"):
    """
    Ejecuta Webots en modo headless dentro de un contenedor Docker.

    :param image_name: Nombre de la imagen Docker de Webots.
    :param world_file: Nombre del archivo .wbt a ejecutar (debe estar en local_worlds_dir).
    :param local_worlds_dir: Ruta local donde están los mundos.
    :param container_name: Nombre opcional del contenedor.
    :return: Logs de la ejecución.
    """
    # Validar que el world existe
    world_path = os.path.join(local_worlds_dir, world_file)
    if not os.path.isfile(world_path):
        raise FileNotFoundError(f"El archivo {world_file} no existe en {local_worlds_dir}")

    # Crear cliente de Docker
    client = docker.from_env()

    # Eliminar contenedor previo si existe
    try:
        old_container = client.containers.get(container_name)
        old_container.stop()
        old_container.remove()
    except docker.errors.NotFound:
        pass

    try:
        print("Iniciando contenedor Docker para Webots...")
        # Ejecutar contenedor
        container = client.containers.run(
            image=image_name,
            name=container_name,
            user=f"{os.getuid()}:{os.getgid()}",
            command=f"""bash -c '
                            Xvfb :99 -screen 0 1280x1024x24 &
                            sleep 2
                            webots --no-rendering --batch --mode=fast --stdout --stderr \"{CONTAINER_WORLD_PATH}/{world_file}\"'
                    """,
            working_dir="/workspace",
            volumes={
                     os.path.abspath(local_worlds_dir): {
                        'bind': CONTAINER_WORLD_PATH, 
                        'mode': 'ro'
                    },
                    os.path.abspath(local_protos): {
                        'bind': CONTAINER_PROTOS_PATH, 
                        'mode': 'ro'
                    },
                    os.path.abspath(local_controllers): {
                        'bind': CONTAINER_CONTROLLERS_PATH, 
                        'mode': 'rw'
                    },
                    os.path.abspath("../train/train_logs"): {
                        'bind': f'{CONTAINER_CONTROLLERS_PATH}/internalTrainingController/train_logs',
                        'mode': 'rw'
                    },
                    os.path.abspath("../train/train_result"): {
                        'bind': f'{CONTAINER_CONTROLLERS_PATH}/internalTrainingController/train_result',
                        'mode': 'rw'
                    }
                },
                
            detach=True,
            tty=True,
            environment={
                "USER": os.getenv("USER", "default"),
                "USERNAME": os.getenv("USER", "default"),
                "DISPLAY": ":99", #En un contenedor Docker sin pantalla física, Xvfb crea una pantalla virtual (normalmente :99 o :1)
                "QT_X11_NO_MITSHM": "1", #
                "QT_QPA_PLATFORM": "xcb", #Webots usa Qt, y necesita especificar cómo comunicarse con el servidor X (Xvfb)
                "LIBGL_ALWAYS_SOFTWARE":"1", #Fuerza a OpenGL a usar renderizado por software (CPU)
                "GALLIUM_DRIVER":"llvmpipe", #llvmpipe es un driver de Mesa que hace renderizado OpenGL usando la CPU de forma eficiente
                "MESA_GL_VERSION_OVERRIDE": "3.3"
            },
            stdout=True,
            stderr=True
        )
        print("Corriendo")
        print("Logs de la simulación:")
        print("-" * 50)
        
        # Buffer para almacenar los bytes que no forman una línea completa
        log_buffer = b''

        # Capturar logs en tiempo real y mostrarlos completos
        for chunk in container.logs(stream=True, follow=True):
            # Añadimos el nuevo chunk de bytes al buffer
            log_buffer += chunk

            # Buscamos saltos de línea ('\n') en el buffer
            while b'\n' in log_buffer:
                # Dividimos el buffer en la primera línea completa y el resto
                line, log_buffer = log_buffer.split(b'\n', 1)
                
                # Decodificamos la línea y la imprimimos
                print(line.decode("utf-8"))

        # Después de que el bucle termine, imprimimos cualquier resto en el buffer
        if log_buffer:
            print(log_buffer.decode("utf-8"))
            
        # Esperar a que termine la simulación
        exit_code = container.wait()
        logs = container.logs().decode("utf-8")
        # Eliminar contenedor al finalizar
        container.remove()

        return {"exit_code": exit_code.get("StatusCode", 1), "logs": logs, "success": exit_code.get("StatusCode", 1) == 0}
    
    except docker.errors.ContainerError as e:
        print(f"Error en la ejecución del contenedor: {e}")
        print("Revisa que el archivo del mundo sea válido y que Webots pueda ejecutarse.")
        
    except docker.errors.ImageNotFound:
        print(f"La imagen '{IMAGE_NAME}' no existe.")
        print("Construye la imagen primero con: docker build -t webots_image .")
        
    except docker.errors.APIError as e:
        print(f"Error en la API de Docker: {e}")
        
    except Exception as e:
        print(f"Error inesperado: {e}")


if __name__ == "__main__":
    # Ejemplo de uso
    resultado = run_webots_world(
        image_name=IMAGE_NAME,
        world_file=WORLD_NAME,
        local_worlds_dir=WORLD_PATH,
        local_protos=PROTOS_PATH,
        local_controllers=CONTROLERS_PATH
    )

    print(f"Éxito: ", resultado['success'])
    print("Código de salida:", resultado["exit_code"])
    
