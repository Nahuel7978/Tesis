import docker
import os

# Configuración
IMAGE_NAME = "webots_image"  # Nombre de tu imagen
WORLD_PATH = "/home/roman7978/Documentos/university_portfolio/Tesis/Autonomous Robot/worlds"  # Ruta absoluta en tu host
WORLD_NAME = "Autonomous Robot.wbt"
CONTAINER_WORLD_PATH = "/workspace/world.wbt"  # Ruta donde lo verá el contenedor

def run_webots_world(image_name, world_file, local_worlds_dir, container_name="webots_headless"):
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
            command=f"xvfb-run -a webots --no-rendering --batch {CONTAINER_WORLD_PATH}/{world_file}",
            volumes={
                os.path.abspath(local_worlds_dir): {
                    'bind': CONTAINER_WORLD_PATH, 
                    'mode': 'ro'
                    }
                },
            detach=True,
            tty=True,
            environment={
                "QT_X11_NO_MITSHM": "1"
            }
        )

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
        local_worlds_dir=WORLD_PATH
    )

    print(f"Éxito: ", resultado['success'])
    print("Código de salida:", resultado["exit_code"])
    print("Logs:")
    print(resultado["logs"])
