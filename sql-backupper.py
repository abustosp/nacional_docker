import os
import re
from dotenv import load_dotenv
from datetime import datetime


# leer variables de entorno
load_dotenv()
sqlpassword = os.getenv("MYSQL_ROOT_PASSWORD")
EXCLUDE_DBS = os.getenv("EXCLUDE_DBS", "").split("|")

directorio = "backups"
hoy_carpeta = datetime.now().strftime("%Y_%m_%d")

# Crear el directorio si no existe
if not os.path.exists(directorio):
    os.makedirs(directorio)
    
# crear el directorio de hoy
hoy_path = os.path.join(directorio, hoy_carpeta)
os.makedirs(hoy_path, exist_ok=True)

# obtener la lista de bases de datos
comando_listar_bases = f'docker exec mysql bash -c "mariadb -u root -p{sqlpassword} -e SHOW DATABASES;"'
bases_de_datos = os.popen(comando_listar_bases).read().strip().split("\n")[1:]
bases_de_datos = [db for db in bases_de_datos if db not in EXCLUDE_DBS]
print("Bases de datos a respaldar:", bases_de_datos)
# hacer el respaldo de cada base de datos
for db in bases_de_datos:
    nombre_archivo = f"{db}.sql"
    ruta_completa = os.path.join(hoy_path, nombre_archivo)
    comando_backup = f'docker exec mysql bash -c "mariadb-dump -u root -p{sqlpassword} {db}" > "{ruta_completa}"'
    os.system(comando_backup)
    print(f"Respaldo de {db} completado y guardado en {ruta_completa}")
print("Respaldo de todas las bases de datos completado.")


