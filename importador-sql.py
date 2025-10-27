#from tkinter.filedialog import askdirectory
import os
import re
from dotenv import load_dotenv
import subprocess


# leer variables de entorno
load_dotenv()
sqlpassword = os.getenv("MYSQL_ROOT_PASSWORD")
motor = os.getenv("MOTOR")
if motor not in ["MYSQL", "MARIADB"]:
    motor = "MARIADB"

#directorio = askdirectory()
directorio = "master"
archivos = os.listdir(directorio)
archivos = [archivo for archivo in archivos if archivo.endswith('.sql')]
# Reemplazar espacios por _ en los nombres de archivos originales y renombrarlos en el sistema de archivos
for archivo in archivos:
    nuevo_nombre = archivo.replace(' ', '_')
    if archivo != nuevo_nombre:
        os.rename(os.path.join(directorio, archivo), os.path.join(directorio, nuevo_nombre))

# Actualizar la lista de archivos con los nuevos nombres
archivos = [archivo.replace(' ', '_') for archivo in archivos]
# Eliminar el archivo creardatabases.sql si existe
if 'creardatabases.sql' in archivos:
    archivos.remove('creardatabases.sql')
archivos = [os.path.join(directorio, archivo) for archivo in archivos]
crear = []
importar = []
for i in archivos:
    # imprimir la database (es lo que precede a "Database: ") (está dentro de las primeras 5 línes)
    i = i.replace('\\', '/')
    print(f'Procesando archivo: {i}')
    with open(i, "rb") as f:  # abrir en modo binario
        for j in range(5):
            # leer la línea en bytes
            linea_bytes = f.readline()
            if not linea_bytes:
                break
            # decodificar con tolerancia a errores
            linea = linea_bytes.decode("utf-8", errors="ignore").strip()

            if "Database: " in linea:
                match = re.search(r"Database: (.+)", linea)
                if match:
                    database = match.group(1)
                    print(f"Base de datos encontrada: {database}")
                break

    # agregar a crear la line f'CREATE DATABASE IF NOT EXISTS {database.replace(" ", "_")}'
    crear.append(f'echo "Creando base de datos: {database}"')

    # crear la base de datos dentro del contenedor usando argumentos en lista para evitar problemas de comillas
    try:
        subprocess.run(
            ['docker', 'exec', '-i', 'mysql',
             'mysql', '-uroot', f'-p{sqlpassword}',
             '-e', f'CREATE DATABASE IF NOT EXISTS `{database.replace("`", "``")}`;'],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error creando base de datos {database}: {e}")

    crear.append('echo "-------------------------------------------------------"')
    # agregar a importar la línea mostrando mensaje y usando stdin para pasar el archivo al cliente mysql dentro del contenedor
    importar.append(f'echo "Importando Base de datos: {database}"')
    file_path = os.path.join('master', i.split('/')[-1])
    try:
        with open(file_path, 'rb') as sqlfile:
            subprocess.run(
                ['docker', 'exec', '-i', 'mysql',
                 'mysql', '-uroot', f'-p{sqlpassword}', database],
                stdin=sqlfile,
                check=True
            )
    except subprocess.CalledProcessError as e:
        print(f"Error importando {file_path} into {database}: {e}")
    except FileNotFoundError:
        print(f"Archivo no encontrado: {file_path}")

    importar.append('echo "-------------------------------------------------------"')
    

# # Exportar crear a sql
# with open('creardb.sh', 'w') as f:
#     f.write("\n".join(crear))
    
# # Exportar importar a sh
# with open('importar.sh', 'w') as f:
#     f.write("\n".join(importar))
