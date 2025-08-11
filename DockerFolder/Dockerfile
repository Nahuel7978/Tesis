# Imagen base con Python 3.10.18
#imagen slim (ligera, sin paquetes innecesarios).
FROM python:3.10.18-slim  

# Variables de entorno para evitar prompts y configurar headless
#--
# Evita que apt-get pida confirmación
ENV DEBIAN_FRONTEND=noninteractive
# Obliga a Webots a renderizar sin interfaz gráfica 
ENV QT_QPA_PLATFORM=offscreen
# Variable estándar de Webots que indica su carpeta de instalación.
ENV WEBOTS_HOME=/usr/local/webots

# Instalar pip en versión compatible
RUN python -m pip install --upgrade pip==22.0.4

# Instalar dependencias del sistema necesarias para Webots y paquetes Python
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    libxkbcommon0 \
    libx11-xcb1 \
    libfontconfig1 \
    libfreetype6 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libsm6 \
    libxi6 \
    libxrandr2 \
    libxss1 \
    libxcursor1 \
    libxinerama1 \
    libusb-1.0-0 \
    libpulse0 \
    libudev1 \
    xvfb \
    bzip2 \
    #Evitar errores de compilación en algunos wheels
    libopencv-dev \
    python3-dev \
    # OpenGL y Mesa para rendering 3D
    libgl1-mesa-dev \
    libgl1-mesa-glx \
    libglu1-mesa \
    libglu1-mesa-dev \
    libegl1-mesa \
    libgles2-mesa \
    mesa-utils \
    libglu1-mesa \
    libosmesa6 \
    libosmesa6-dev \
    # Dependencias Qt completas para offscreen rendering
    qt5-qmake \
    qtbase5-dev \
    qtbase5-dev-tools \
    libqt5gui5 \
    libqt5core5a \
    libqt5widgets5 \
    libqt5opengl5 \
    libqt5opengl5-dev \
    qt5-gtk-platformtheme \
    qt5-style-plugins \
    && rm -rf /var/lib/apt/lists/*

# Descargar e instalar Webots headless (última versión estable)
RUN wget -q https://github.com/cyberbotics/webots/releases/download/R2023b/webots-R2023b-x86-64.tar.bz2 && \
    tar -xjf webots-R2023b-x86-64.tar.bz2 && \
    mv webots /usr/local/webots && \
    rm webots-R2023b-x86-64.tar.bz2

# Añadir Webots al PATH
ENV PATH="${WEBOTS_HOME}:${PATH}"
# Configurar variables de entorno para Webots
ENV QT_X11_NO_MITSHM=1
ENV QT_DEBUG_PLUGINS=0
ENV LIBGL_ALWAYS_INDIRECT=1
ENV MESA_GL_VERSION_OVERRIDE=3.3
ENV QT_LOGGING_RULES="*=false"
# Copiar el archivo requirements.txt con las dependencias de Python
COPY requirements.txt /tmp/requirements.txt

# Instalar dependencias de Python
RUN pip install --no-deps gym==0.21.0 && \
    pip install numpy pillow && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Crear carpeta de trabajo
WORKDIR /workspace

# Comando por defecto: abrir bash
CMD ["/bin/bash"]
