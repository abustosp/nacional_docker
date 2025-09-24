#!/bin/bash
# run-sql-backupper.sh
# Script para activar el entorno virtual .venv y ejecutar sql-backupper.py

# Salir si ocurre un error
set -e

# Ir al directorio del proyecto (modificar si hace falta)
cd "$(dirname "$0")"

# Activar entorno virtual
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "No se encontró el entorno virtual en .venv"
    exit 1
fi

# Ejecutar el script de backup
python sql-backupper.py
