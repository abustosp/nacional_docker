#!/bin/bash

# Habilitar modo estricto para capturar errores y gestionar variables no definidas
set -euo pipefail

# Actualizar lista de paquetes e instalar Docker
echo "Actualizando lista de paquetes..."
sudo apt update

# Instalar req.txt
echo "Instalando python-dotenv en un entorno virtual..."
sudo apt install python3-venv -y
python3 -m venv .venv
source ./.venv/bin/activate
sudo apt install python3-pip -y
pip3 install -r req.txt


# Instalar Docker
echo "Instalando docker.io y docker-compose-v2..."
sudo apt install -y docker.io docker-compose-v2

# Agregar el usuario actual al grupo docker para evitar usar sudo con docker
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

# Levantar los contenedores Docker
echo "Levantando los contenedores Docker..."
docker compose up -d

# Esperar 15 segundos
echo "Esperando 15 segundos para asegurar que los contenedores se han levantado..."
sleep 15

# Ejecutar script de Python que crea e importa las bases de datos
echo "Ejecutando importador-sql.py..."
python3 importador-sql.py

echo "Proceso completado."

