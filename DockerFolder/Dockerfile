# Imagen base con Python 3.10.18
FROM python:3.10.18-slim  

# Variables de entorno para evitar prompts y configurar headless
ENV DEBIAN_FRONTEND=noninteractive
ENV WEBOTS_HOME=/usr/local/webots

# Instalar pip en versión compatible
RUN python -m pip install --upgrade pip==22.0.4

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    # Herramientas básicas
    wget unzip curl git bzip2 xauth \
    # X11 y Xvfb
    xvfb x11-utils \
    # Librerías base del sistema
    libgl1 libglib2.0-0 libxkbcommon0 libx11-xcb1 \
    libfontconfig1 libfreetype6 libx11-6 libxext6 \
    libxrender1 libsm6 libxi6 libxrandr2 libxss1 \
    libxcursor1 libxinerama1 libusb-1.0-0 libpulse0 libudev1 \
    # OpenGL y Mesa (CLAVE para renderizado por software)
    mesa-utils mesa-utils-extra mesa-common-dev \
    libgl1-mesa-dev libgl1-mesa-glx libgl1-mesa-dri \
    libglu1-mesa libglu1-mesa-dev \
    libegl1-mesa libgles2-mesa \
    libosmesa6 libosmesa6-dev \
    # DRM drivers
    libdrm2 libdrm-common libdrm-amdgpu1 libdrm-intel1 libdrm-nouveau2 \
    # Qt5 completo
    qt5-qmake qtbase5-dev qtbase5-dev-tools \
    libqt5gui5 libqt5core5a libqt5widgets5 \
    libqt5opengl5 libqt5opengl5-dev \
    qt5-gtk-platformtheme qt5-style-plugins \
    # Dependencias adicionales XCB
    libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 \
    libxi-dev libxmu-dev libxmu6 libxpm-dev \
    # Python y OpenCV
    libopencv-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Descargar e instalar Webots headless
RUN wget -q https://github.com/cyberbotics/webots/releases/download/R2023b/webots-R2023b-x86-64.tar.bz2 && \
    tar -xjf webots-R2023b-x86-64.tar.bz2 && \
    mv webots /usr/local/webots && \
    rm webots-R2023b-x86-64.tar.bz2

# Añadir Webots al PATH
ENV PATH="${WEBOTS_HOME}:${PATH}"

# Variables de entorno para renderizado por software
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV GALLIUM_DRIVER=llvmpipe
ENV MESA_GL_VERSION_OVERRIDE=3.3
ENV QT_X11_NO_MITSHM=1
ENV QT_DEBUG_PLUGINS=0
ENV QT_LOGGING_RULES="*=false"
# REMOVER QT_QPA_PLATFORM para evitar conflictos

# Copiar requirements.txt
COPY requirements.txt /tmp/requirements.txt

# Instalar dependencias de Python
RUN pip install --no-deps gym==0.21.0 && \
    pip install numpy pillow && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Crear carpeta de trabajo
WORKDIR /workspace

# Comando por defecto
CMD ["/bin/bash"]