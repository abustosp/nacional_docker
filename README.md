# Instalación del Sistema nacional en Servidores

Para poder instalar el Nacional en un servidor VPS, vamos a tener que seguir una serie de pasos que los iré explicando en distintas secciones, algunas pueden realizarse en distinto orden.

Recomiendo utilizar Ubuntu como SO para el servidor, igualmente en teoría el instalador está dockerizado y debería funcionar sin problemas en otros SO.

Se puede utilizar tanto la IP Fija de los servicios de servidores (importante tenerla en cuenta para la conexión) como un dominio y la utilización de un Reverse Proxy para no "Acordarnos de esta dirección de IP"

## Descarga de este repositorio de github

Si tenemos git lo descargamos con `git clone https://github.com/abustosp/Nacional_Docker.git`, sinó podemos hacer click en code y `Download ZIP`.

## Descarga de los archivos necesarios de Nacional

1. Desde la página oficial de [Nacional](https://nacionalsoft.com/) vamos a Descargas y después bajamos el [Nacional Sistema versión de 64 bits](https://nacionalsoft.com/file/Nacional_Sistema_1.7.0_64bit_install.exe).

2. Extraemos los binarios, esto lo hacemos con click derecho en el archivo descargado y dependiendo del archivador de ficheros que usemos podemos tener disitntas opciones (recomiendo usar [7Zip](https://www.7-zip.org/) que es gratis y de código abierto).

3. Copiamos/movemos las Carpetas de `server` y `client` a la descargada del repositorio.

4. Copiamos/movemos la base `master.sql` (que se encuentra en `$EXEDIR`) a `master` del repositorio.

5. Copiamos nuestra licencia en la `carpeta server/cfg` 

6. editamos el archivo `.env` y hacemos lo siguiente:
   - Acutalizamos la contraseña de la Base de datos en la variable `MYSQL_ROOT_PASSWORD=`
   - Debemos elegir el motor de base de datos, puede ser `MYSQL` o `MARIADB`, por defecto está `MARIADB`, si queremos usar `MYSQL` lo cambiamos en la variable `MOTOR=`
   - Excluimos las bases de datos que no queremos que se hagan backup en la variable `EXCLUDE_DBS=`, separando los nombres con `|` (por ejemplo `EXCLUDE_DBS=information_schema|performance_schema|mysql|sys` para excluir las bases de datos del sistema) (Opcional)

7. Modificamos el archivo `server/cfg/nacional.cfg` con el editor de texto que prefiramos cambiamos los siguientes valores:
   - `net.host=localhost` por `net.host=0.0.0.0`
   - `web.host=`por `web.host=0.0.0.0`
   - `web.port=` por `web.port=8080`
   - `db.host=localhost` por `db.host=LAP_IP_PÚBLICA_DEL_SERVIDOR`
   - `db.password=root` por `db.password=LA_CLAVE_DE_LA_BASE_DE_DATOS_DEL_.env`


## Preparación del servidor

1. Instalamos docker, podemos hacerlo con `apt install docker.io docker-compose-v2 -y` (en otros SO puede cambiar ligeramente el comando y puede no existir la dependencia de docker-compose-v2)

2. Copiamos toda la carpeta preparada anteriormente (la que posee los archivos extraídos con la licencia) al servidor, para esto hay muchas formas, la mas "sencilla" para los no programadores es usar [WinSCP](https://winscp.net/eng/index.php).

3. Una vez copiada la carpeta abrimos con conectamos por SSH al servidor y hacemos lo siguiente:
   
   1. Vamos a la carpeta con los archivos `cd NombreDeTuCarpeta`

   2. Editamos el docker-compose.yml para seleccionar el motor de base de datos que queremos usar (MYSQL o MARIADB), si dejamos el que viene por defecto es MARIADB, si queremos usar MYSQL debemos comentar la linea que comienza con `image: mariadb` y descomentar la linea que comienza con `image: mysql`.
   
   3. Instalamos el nacional, tenemos 2 opciones:
      
      1. Corremos `bash installation.sh`, para hacer una instalación un poco mas automatizada
      
      2. Corremos `docker compose up -d` y luego que se creen los contenedores realizar la importación de las bases de datos Master y backups con `python3 listador-sql.py` (para crear los archivos de importación), `bash creardb.sh` (para crear las bases de datos) y `bash importar.sh` (para importar los datos).

## Configuración de MariaDB compatible con Nacional

Nacional crea algunas tablas sin indicar el juego de caracteres y otras tablas en `latin1`. Para evitar errores al crear claves foráneas, como `errno: 150 "Foreign key constraint is incorrectly formed"`, el servicio `mysql` de `docker-compose.yml` configura MariaDB con estos valores:

```text
bind_address=0.0.0.0
character_set_server=latin1
collation_server=latin1_swedish_ci
max_connections=151
sql_mode=STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION
```

`max_connections=151` es el valor por defecto de la imagen utilizada y no se aumenta sin medir antes el consumo y la cantidad real de conexiones. Tampoco es necesario eliminar `ONLY_FULL_GROUP_BY`, porque no forma parte del `sql_mode` configurado.

La configuración debe realizarse en `docker-compose.yml`, no en los archivos `/etc/mysql/...` del servidor host, porque MariaDB se ejecuta dentro de Docker.

### Aplicar la configuración a una instalación existente

1. Copiar la licencia correspondiente en `server/cfg` antes de reiniciar Nacional Server.
2. Crear un backup antes de modificar o recrear contenedores:

   ```bash
   ./run-sql-backupper.sh
   ```

3. Validar la configuración de Compose:

   ```bash
   docker compose config
   ```

4. Recrear los contenedores conservando el volumen persistente `./mysql`:

   ```bash
   docker compose up -d --force-recreate
   ```

No eliminar la carpeta `./mysql` durante este procedimiento. Las bases existentes no deben convertirse masivamente: los dumps y tablas históricas de Nacional ya utilizan `latin1`.

### Verificar la configuración efectiva

```bash
docker exec mysql mariadb -uroot -p -e "
SHOW VARIABLES WHERE Variable_name IN (
  'bind_address',
  'character_set_server',
  'collation_server',
  'max_connections',
  'sql_mode'
);"
```

Los resultados esperados son `0.0.0.0`, `latin1`, `latin1_swedish_ci`, `151` y el `sql_mode` indicado anteriormente.

Para auditar bases con tablas mezcladas entre `latin1` y `utf8mb4`:

```bash
docker exec mysql mariadb -uroot -p -e "
SELECT TABLE_SCHEMA, TABLE_COLLATION, COUNT(*) AS tables_count
FROM information_schema.TABLES
WHERE TABLE_SCHEMA NOT IN ('information_schema','mysql','performance_schema','sys')
GROUP BY TABLE_SCHEMA, TABLE_COLLATION
ORDER BY TABLE_SCHEMA, TABLE_COLLATION;"
```

Si una base creada de forma incompleta tiene tablas con distintas collations, respaldarla si contiene datos útiles, eliminarla desde Nacional y volver a copiarla después de aplicar la configuración.

Después de copiar una base desde el cliente, verificar `sys_group`, `sys_permission` y su clave foránea reemplazando `Juan Romero` por el nombre correspondiente:

```bash
docker exec mysql mariadb -uroot -p -e "
SELECT TABLE_NAME, TABLE_COLLATION
FROM information_schema.TABLES
WHERE TABLE_SCHEMA='Juan Romero'
  AND TABLE_NAME IN ('sys_group','sys_permission');

SELECT CONSTRAINT_NAME, TABLE_NAME, REFERENCED_TABLE_NAME
FROM information_schema.REFERENTIAL_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA='Juan Romero'
  AND TABLE_NAME='sys_permission';"
```

Ambas tablas deben usar `latin1_swedish_ci` y `sys_permission` debe referenciar `sys_group`.

### Acceso remoto a MariaDB

El puerto `3306:3306` y `bind-address=0.0.0.0` permiten conexiones remotas. Esto publica MariaDB en las interfaces de red del servidor, por lo que se debe restringir el puerto `3306` mediante el firewall del proveedor o del sistema operativo para aceptar solamente las IPs autorizadas.

Referencias técnicas:

- [Configuración de la imagen oficial MariaDB](https://hub.docker.com/_/mariadb)
- [Charsets y collations en MariaDB](https://mariadb.com/docs/server/reference/data-types/string-data-types/character-sets/setting-character-sets-and-collations)
- [Requisitos de claves foráneas](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/optimization-and-indexes/foreign-keys)
- [Seguridad al publicar puertos Docker](https://docs.docker.com/engine/network/port-publishing/)

## Preparación de las maquinas cliente (las que se conectan al servidor)

1. Instalamos nacional con el instalador previamente descargado.

2. Copiamos nuestra licencia en la `carpeta server/cfg`.

3. para conectar ponemos la `IP del Servidor contratado` o el `Dominio` ( ejemplo.com.ar si realizamos el Reverse Proxy) en `Opciones` y `Servidor`.

# Tips

- Modificar los puertos del `docker-compose.yml` (recordar usar el mismo en el cliente), el puerto 3306 es el más común para el uso de MySQL, si dejamos el puerto “normal” por defecto es más probable que algún atacante pueda encontrar una vulnerabilidad y copiarlas/borrarlas

- modificar las claves por defecto (`root`), si dejamos la original estamos dejando las bases de manera muy insegura y cualquiera podría acceder.

- Restringir el ingreso a MariaDB a IPs autorizadas mediante firewall. No dejar el puerto `3306` abierto a todo Internet.

# Automatizar Backups

Para automatizar los backups podemos usar el script `run-sql-backupper.sh` que se encuentra en la carpeta `scripts`, este script activa un entorno virtual de python, y ejecuta el script `sql-backupper.py` que realiza el backup de las bases de datos en la carpeta `backups` (dentro de la carpeta del proyecto).

## Cronjob

Para automatizar la ejecución del script podemos usar un cronjob, para esto editamos el crontab con `crontab -e` y agregamos la siguiente línea para que se ejecute todos los días a las 0 AM:

``` cron
 0 0 * * * cd /docker/nacional_docker && ./run-sql-backupper.sh 
 ```
Si el usuario es root (recomendado) la línea sería:
 ``` cron
 0 0 * * * bash -c "cd /root/docker/nacional_docker && ./run-sql-backupper.sh"
```
