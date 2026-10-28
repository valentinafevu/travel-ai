# Oracle Autonomous Database · aterrizar

Esta carpeta contiene la configuración privada de la base de datos. El wallet y
`connection.json` están excluidos de Git y nunca se envían al frontend.

## Cuando exista la base

1. Descarga el wallet de la instancia Autonomous Database y descomprímelo en `wallet/`.
   Deben existir `wallet/tnsnames.ora` y `wallet/ewallet.pem` (conserva también los otros
   archivos descargados). El driver funciona en modo Thin, sin Oracle Instant Client.
2. Copia `connection.example.json` a `connection.json` y completa:
   - `user`: usuario de la base de datos destinado a la aplicación.
   - `password`: contraseña de ese usuario.
   - `dsn`: alias exacto del archivo `tnsnames.ora`, por ejemplo `aterrizar_low`.
   - `wallet_password`: contraseña elegida al descargar el wallet.
3. El usuario debe poder abrir sesiones, crear las tablas e índices de Django y tener
   cuota en su tablespace. La red desde la que se ejecuta Django debe poder llegar al
   endpoint de la instancia. La configuración usa mTLS y verifica el certificado.
4. Desde la raíz del proyecto:

```bash
mm activate "$PWD/venv"
python -m pip install -r travel-app/requirements.txt
DATABASE_BACKEND=oracle python travel-app/manage.py check_oracle
DATABASE_BACKEND=oracle python travel-app/manage.py migrate
DATABASE_BACKEND=oracle python travel-app/manage.py seed_demo
DATABASE_BACKEND=oracle python travel-app/manage.py check_oracle --check-data
```

Después reinicia Django. En modo predeterminado (`DATABASE_BACKEND=auto`), la presencia
de `connection.json` selecciona Oracle para todos los modelos y endpoints. No necesitas
cambiar Vue. Si el archivo existe pero es inválido, o el wallet está incompleto, Django
falla con un mensaje de configuración: no vuelve silenciosamente a SQLite.

Sin `connection.json`, la demo sigue usando SQLite. Puedes fijar `DATABASE_BACKEND=sqlite`
para pruebas locales o `DATABASE_BACKEND=oracle` para exigir Oracle aun cuando falten
archivos. La configuración se lee al arrancar, no en cada petición. Añadir solo el wallet
no basta: también se necesitan el usuario, su contraseña y el alias de conexión.

La base nueva inicia vacía. `migrate` crea las tablas y `seed_demo` carga los datos
ficticios; no se copian automáticamente los datos existentes de SQLite.

## Vectores

`Traveler`, `Flight` y `Accommodation` tienen un campo persistente `vector` con pesos
de intereses (`lujo`, `economico`, `grupo`, `aventura`, `playa`) entre 0 y 1. Django lo
guarda mediante `JSONField`, compatible con Oracle. La API devuelve estos vectores y
el vector promedio del paquete; la similitud coseno se calcula en Python.

Este diseño no utiliza el tipo SQL `VECTOR`, índices vectoriales ni `VECTOR_DISTANCE`.
Eso requeriría una migración específica y definir las dimensiones de los embeddings.

## Verificación

`check_oracle` abre una conexión real y ejecuta `SELECT 1 FROM DUAL`. Con `--check-data`
también consulta las tres tablas y valida los vectores existentes. No modifica datos.
Sin una instancia y credenciales reales solo se pueden verificar la configuración,
el driver y las pruebas locales; no se puede confirmar la conexión remota.

Las claves de la API de OCI (`~/.oci/config`, OCID, clave privada) son credenciales del
plano de administración y no sustituyen al usuario/contraseña/wallet de esta conexión.

Referencias: [Django y Oracle](https://docs.djangoproject.com/en/5.2/ref/databases/#oracle-notes),
[conexión a Autonomous Database](https://python-oracledb.readthedocs.io/en/stable/user_guide/connection_handling.html#connecting-to-oracle-cloud-autonomous-databases),
[JSONField](https://docs.djangoproject.com/en/5.2/ref/models/fields/#jsonfield).
