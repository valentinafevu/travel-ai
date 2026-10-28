# aterrizar · Paquetes de viaje personalizados

Demo con **Django 5.2 + Oracle Autonomous Database (SQLite mientras no haya credenciales)** en `travel-app/` y **Vue 3 + Vite** en `travel-web/`.
El selector cambia entre Camila (lujo), Diego (grupo económico) y Sofía (aventura).
La API genera los dos paquetes más afines para cada perfil; cada paquete contiene
**un alojamiento, un vuelo de ida y un vuelo de vuelta**.

## Ejecutar

Desde la raíz del proyecto, activa el entorno micromamba existente:

```bash
mm activate "$PWD/venv"
python -m pip install -r travel-app/requirements.txt
python travel-app/manage.py migrate
python travel-app/manage.py seed_demo
python travel-app/manage.py runserver 127.0.0.1:8000
```

En otra terminal, también desde la raíz:

```bash
mm activate "$PWD/venv"
cd travel-web
npm install
npm run dev -- --host 127.0.0.1
```

Abre <http://127.0.0.1:5173>. Vite envía las peticiones `/api/` a Django en el puerto 8000;
ambos procesos deben estar ejecutándose. El frontend no contiene una copia del catálogo.
Python requiere 3.10 o superior y Node `^22.18.0 || >=24.12.0`.

Si `mm` no está disponible en una terminal no interactiva, inicializa micromamba:

```bash
eval "$(micromamba shell hook --shell zsh)"
function mm() { micromamba "$@"; }
mm activate "$PWD/venv"
```

## Datos de demostración

`travel-app/travel/data/demo.json` contiene 3 usuarios, 6 alojamientos y 12 vuelos
ficticios. Todos los viajeros parten de Medellín (MDE). Las fechas se generan a partir
de 30 días después de ejecutar `seed_demo`. Se pueden fijar explícitamente:

```bash
python travel-app/manage.py seed_demo --start-date 2026-12-01
```

Repetir el comando actualiza los registros de la demo sin duplicarlos; no elimina
otros registros de la base. Para cambiar perfiles o inventario, edita el JSON y vuelve
a ejecutar el comando. Los viajes pasados se excluyen, así que conviene actualizar
las fechas si la demo lleva tiempo sin ejecutarse.

Los importes son **USD por persona**. El precio del alojamiento cubre toda la estancia.
El total del paquete suma alojamiento + ida + vuelta; el total del grupo multiplica
esa suma por el número de viajeros. Los traslados terrestres no se incluyen.
Las fechas y horas se interpretan en `America/Bogota`, apropiado para este catálogo
doméstico colombiano.

## Lógica de recomendaciones

1. Filtra alojamientos por capacidad y fecha futura, y vuelos por asientos y salida futura.
2. Combina vuelos que parten del origen del usuario y llegan al aeropuerto del alojamiento
   el día de entrada. La vuelta sale de ese aeropuerto el día de salida y regresa al origen.
3. Descarta combinaciones cuyo precio total por persona supera el presupuesto.
4. Promedia los vectores de los tres componentes con el mismo peso y calcula la similitud
   coseno con el vector del usuario (`lujo`, `economico`, `grupo`, `aventura`, `playa`).
5. Ordena por afinidad descendente, luego por menor precio y por ID para resolver empates.

Los paquetes se calculan a partir del inventario; no son relaciones fijas guardadas por
usuario. El porcentaje de afinidad representa similitud de intereses, no una probabilidad
de compra. La búsqueda en memoria es adecuada para este catálogo pequeño.

## API

| Método | Ruta | Respuesta |
| --- | --- | --- |
| GET | `/api/users/` | `users` y `vector_dimensions` |
| GET | `/api/users/camila/recommendations/` | `user`, `currency` y `recommendations` |
| GET | `/api/users/diego/recommendations/?limit=5` | Hasta 5 combinaciones; límite válido de 1 a 20 |

Cada recomendación incluye `accommodation`, `outbound_flight`, `return_flight`,
`score`, `nights`, `price_per_person_usd` y `total_price_usd`. Los importes se serializan
como cadenas decimales para conservar su precisión; las fechas usan ISO 8601 y las
horas incluyen el desplazamiento UTC. Un usuario desconocido devuelve 404 JSON y
un límite inválido devuelve 400 JSON. Si no hay opciones válidas, devuelve 200 con
`recommendations: []`. Los métodos de escritura devuelven 405.

## Verificar

Desde la raíz, con micromamba activado:

```bash
python travel-app/manage.py check
python travel-app/manage.py test travel
cd travel-web
npm run build
```

Las pruebas cubren composición, precio, capacidad, fechas, rutas, ranking, errores
de API y carga repetida del catálogo. La interfaz incluye carga, reintento, estado vacío
y cancelación de peticiones al cambiar de perfil.

## Alcance

Es una demo local con perfiles públicos ficticios, sin autenticación, reservas ni integración
con proveedores de viajes. Para usar datos personales reales debe agregarse autenticación
y autorización por usuario. Para desplegar, configura `DJANGO_DEBUG=0`,
`DJANGO_SECRET_KEY` y `DJANGO_ALLOWED_HOSTS`, y sirve `travel-web/dist/` con un servidor
web que redirija `/api/` al servidor WSGI de Django. `runserver` es para desarrollo.

## Oracle Autonomous Database

Coloca las credenciales en `travel-app/credentials/oracle/connection.json` y el wallet
descomprimido en `travel-app/credentials/oracle/wallet/`. Al reiniciar, Django selecciona
Oracle automáticamente. Sigue la [guía de conexión](travel-app/credentials/oracle/README.md)
para preparar las tablas, cargar datos y comprobar la conexión real.

Los campos `vector` de usuarios, vuelos y alojamientos se persisten como JSON en Oracle.
La API también devuelve el vector promedio de cada paquete. La afinidad se calcula en
Django; no se usa aún el tipo SQL `VECTOR` ni búsqueda vectorial dentro de Oracle.

Para ejecutar todas las pruebas sin depender de credenciales:

```bash
DATABASE_BACKEND=sqlite python travel-app/manage.py test travel config
```
