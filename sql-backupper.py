import os
import re
from dotenv import load_dotenv
from datetime import datetime
import mysql.connector


# leer variables de entorno
load_dotenv()
sqlpassword = os.getenv("MYSQL_ROOT_PASSWORD")
EXCLUDE_DBS = os.getenv("EXCLUDE_DBS", "").split("|")
motor = os.getenv("MOTOR")
if motor not in ["MYSQL", "MARIADB"]:
    motor = "MARIADB"

directorio = "backups"
hoy_carpeta = datetime.now().strftime("%Y_%m_%d__%H_%M_%S")

# Crear el directorio si no existe
if not os.path.exists(directorio):
    os.makedirs(directorio)
    
# crear el directorio de hoy
hoy_path = os.path.join(directorio, hoy_carpeta)
os.makedirs(hoy_path, exist_ok=True)

# obtener la lista de bases de datos

# Conectar a la base de datos MySQL usando mysql-connector-python
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=sqlpassword
)
cursor = conn.cursor()
cursor.execute("SHOW DATABASES;")
bases_de_datos = [db[0] for db in cursor.fetchall() if db[0] not in EXCLUDE_DBS and db[0] != "DATABASES"]
cursor.close()
conn.close()
bases_de_datos = [db for db in bases_de_datos if db not in EXCLUDE_DBS and db != "DATABASES"]

print("---------------------------------------")
print("Bases de datos a respaldar:", bases_de_datos)
print("---------------------------------------")

# hacer el respaldo de cada base de datos
for db in bases_de_datos:
    nombre_archivo = f"{db}_{hoy_carpeta}.sql"
    ruta_completa = os.path.join(hoy_path, nombre_archivo)
    db = f"'{db}'"
    comando_crear_carpeta = f'docker exec mysql bash -c "mkdir -p /backups/{hoy_carpeta}"'
    if motor == "MYSQL":
        comando_backup = f'docker exec mysql bash -c "mysqldump -uroot -p{sqlpassword} {db}" > "{ruta_completa}"'
    else:
        comando_backup = f'docker exec mysql bash -c "mariadb-dump -uroot -p{sqlpassword} {db}" > "{ruta_completa}"'
    os.system(comando_crear_carpeta)
    os.system(comando_backup)
    print(f"Respaldo de {db} completado y guardado en {ruta_completa}")
print("---------------------------------------")
print("Respaldo de todas las bases de datos completado.")

# hacer un tar.gz de la carpeta creada y eliminar la original
tar_filename = f"backups_{hoy_carpeta}.tar.gz"
tar_filepath = os.path.join(directorio, tar_filename)
comando_tar = f'tar -czf "{tar_filepath}" -C "{directorio}" "{hoy_carpeta}"'
os.system(comando_tar)
# eliminar la carpeta original
comando_eliminar_carpeta = f'rm -rf "{hoy_path}"'
os.system(comando_eliminar_carpeta)
print(f"Archivo comprimido creado: {tar_filepath}")
print("Carpeta original eliminada.")
print("---------------------------------------")
print("Proceso de respaldo finalizado.")