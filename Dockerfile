# =============================================================================
# Dockerfile: Climate Data Tools (CDT v8.0) & Python Orchestrator
# Multi-platform: Linux x86_64 / ARM64 (Apple Silicon)
# Base: rocker/geospatial:4.4 (R 4.4 + GDAL + GEOS + PROJ + NetCDF + UDUNITS2)
# =============================================================================

FROM rocker/geospatial:4.4.2

LABEL maintainer="Climate Data Tools Automation Team"
LABEL description="CDT v8.0 R-Spatial Runtime + Python Experiment Launcher & Benchmark Suite"

# Evitar prompts interactivos durante la instalación
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# 1. Instalar dependencias de sistema para Python, Fortran y herramientas C/C++
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    gfortran \
    git \
    curl \
    wget \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libfontconfig1-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar paquetes de R requeridos por CDT v8.0 desde CRAN / RSPM
RUN install2.r --error --skipinstalled -n -1 \
    matrixStats \
    fields \
    lmomco \
    fitdistrplus \
    ADGofTest \
    qmap \
    dynamicTreeCut \
    doParallel \
    foreach \
    doSNOW \
    R.utils \
    reshape2 \
    latticeExtra \
    RColorBrewer \
    gridBase \
    jsonlite \
    XML \
    xml2 \
    urltools \
    curl \
    httr \
    rvest \
    stringr \
    stringi \
    units \
    future \
    devtools \
    pkgbuild \
    && rm -rf /tmp/downloaded_packages

# 3. Crear directorio de trabajo
WORKDIR /workspace

# 4. Copiar código fuente de CDT (para compilar las rutinas Fortran y C nativas)
COPY DESCRIPTION NAMESPACE Makevars* ./
COPY R/ ./R/
COPY src/ ./src/

# 5. Compilar e instalar el paquete CDT v8.0 en la librería de R del sistema
RUN R CMD INSTALL . --no-staged-install && \
    Rscript -e "if (!require('CDT')) stop('Fallo en la instalación de CDT')"

# 6. Configurar entorno virtual de Python y dependencias
COPY requirements.txt ./
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 7. Copiar el resto del repositorio
COPY . .

# 8. Variables de entorno de ejecución
ENV PYTHONUNBUFFERED=1
ENV R_LIBS_USER=/usr/local/lib/R/site-library
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# 9. Comando por defecto: verificación del entorno
CMD ["python", "launcher/experiment_runner.py", "--check-env"]
