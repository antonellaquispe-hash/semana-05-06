# DAE — Movie Management System

Sistema de gestión y catálogo público de películas construido con Django.

El proyecto reúne dos partes: un **catálogo público** donde se consultan las
películas del catálogo, agrupadas por género y ordenadas por puntuación media, y
un **Django Admin** donde se gestionan los géneros, las personas (directores), las
películas y las valoraciones que alimentan ese catálogo.

El contenido no se crea con el sitio público: se registra desde el Admin, y las
páginas lo muestran de forma inmediata.

## Tecnologías

- **Python 3.12+**
- **Django 5.2**
- **SQLite** como base de datos (vía `db.sqlite3`, que no se versiona)
- **Pillow**, necesario para el `ImageField` del cartel de cada película
- **Plantillas de Django** para toda la capa de presentación
- **CSS estático** en `static/css/movies.css`

No hay dependencias de frontend ni paso de compilación: el CSS es un único
archivo escrito a mano y las plantillas son las de Django.

## Estructura del proyecto

Rutas completas de los archivos del proyecto:

```
manage.py                                          # Utilidad de línea de comandos de Django
requirements.txt                                   # Dependencias de Python
README.md

DAE/settings.py                                    # Configuración del proyecto
DAE/urls.py                                        # URLs raíz (incluye el Admin)
DAE/asgi.py
DAE/wsgi.py

movies/models.py                                   # Genre, Person, Movie, Rating
movies/forms.py                                    # Formularios del Admin, búsqueda y valoración
movies/views.py                                    # Vistas: catálogo, ficha y listado por género
movies/urls.py                                     # Rutas del catálogo (app_name = "movies")
movies/admin.py                                    # Registro en Django Admin
movies/tests.py                                    # Pruebas del catálogo público
movies/apps.py

movies/templates/movies/base.html                  # Base: navegación, cabecera y bloques
movies/templates/movies/_movie_card.html           # Fragmento reutilizable de la tarjeta
movies/templates/movies/recommendations.html       # Catálogo agrupado por género
movies/templates/movies/movie_detail.html          # Ficha con valoraciones y formulario
movies/templates/movies/genre_detail.html          # Listado de las películas de un género

static/css/movies.css                              # Hoja de estilos del catálogo
media/                                             # Carteles subidos desde el Admin
db.sqlite3                                         # Base de datos de desarrollo (no versionada)
```

Además, `movies/migrations/` contiene las migraciones del proyecto
(`0001_initial.py` y `0002_alter_genre_options_alter_movie_options_and_more.py`).

### Los cuatro modelos

| Modelo   | Para qué sirve                                             |
| -------- | ---------------------------------------------------------- |
| `Genre`  | Categoría temática de las películas, con nombre único          |
| `Person` | Persona de la producción; como `director` de una película  |
| `Movie`  | Película con su año, duración, cartel, géneros y director   |
| `Rating` | Puntuación de 1 a 10 y comentario opcional sobre una película |

Los cuatro guardan además `created_at` y `updated_at` para auditoría.

## Motor de plantillas

La presentación entera se construye con el motor de plantillas de Django.

- **Herencia** — las tres páginas de contenido (`recommendations.html`,
  `movie_detail.html` y `genre_detail.html`) hacen `{% extends "movies/base.html" %}`.
- **Bloques** — `base.html` define `{% block title %}`, `{% block description %}`,
  `{% block heading %}`, `{% block subtitle %}` y `{% block content %}`, que cada
  página sobrescribe con lo que le es propio.
- **Fragmentos reutilizables** — `{% include "movies/_movie_card.html" %}`. La tarjeta
  de película está definida una sola vez y la reutilizan el catálogo, la ficha y el
  listado por género. La ficha nunca copia ese HTML.
- **Variables de contexto** — `{{ movie.title }}`, `{{ genre.description }}`,
  `{{ movie.average_score }}`, `{{ movie.ratings_count }}`, `{{ genre.movie_count }}`.
- **Bucles** — `{% for %}` para recorrer películas, géneros y valoraciones.
- **Estado vacío** — `{% empty %}` en el catálogo y en el listado por género, con
  un mensaje propio cuando no hay nada que mostrar.
- **Condicionales** — `{% if %}` para el cartel, la insignia de "Top", la barra de
  puntuación y el bloque de valoraciones.
- **Filtros** — `slugify` para las clases CSS de género, `floatformat` para la nota
  media, `default_if_none` para la barra sin puntuación y `blocktranslate` para los
  textos con cantidad.
- **URLs** — `{% url "movies:recommendations" %}`, `{% url "movies:movie_detail" pk=… %}`
  y `{% url "movies:genre_detail" genre_pk=… %}`. Ninguna ruta está escrita a mano en el HTML.
- **Archivos estáticos** — `{% load static %}` y `{% static "css/movies.css" %}`.
- **`unlocalize` para CSS** — el ancho de la barra de puntuación se escribe dentro de
  un `calc()` de CSS, que exige siempre punto decimal. Con `LANGUAGE_CODE = "es"` un
  `{{ movie.average_score }}` a secas se renderiza como `8,0` y produciría
  `calc(8,0 * 10%)`, que el navegador descarta por no ser válido. El filtro
  `|unlocalize` deja el separador en su forma invariante.

### El fragmento `_movie_card.html`

Acepta `movie` y dos parámetros opcionales:

- `heading_level` — nivel del encabezado del título; por defecto `"3"` en los
  listados y `"2"` en la ficha.
- `link_genres` — convierte cada chip de género en un enlace al listado de su
  género. Sólo lo activa la ficha, que es la única plantilla donde la tarjeta no
  está ya dentro de su propio `<a class="card-link">`. En los dos listados los
  chips se quedan como `<span>`: anidar un `<a>` dentro de otro `<a>` es HTML
  inválido y el navegador cerraría el enlace externo antes de los chips.

Espera que la película tenga disponibles `average_score` y `ratings_count`. Las
anotaciones las añade `movies.views.with_rating_stats()` en una sola consulta, así
que la tarjeta no dispara consultas adicionales.

## Rutas públicas

Definidas en `movies/urls.py`, bajo el espacio de nombres `movies`:

| Nombre                    | Ruta                | Página                                    |
| ------------------------- | ------------------- | ----------------------------------------- |
| `movies:recommendations`  | `/movies/`          | Catálogo agrupado por género              |
| `movies:movie_detail`     | `/movies/<int:pk>/` | Ficha de una película con sus valoraciones |
| `movies:genre_detail`     | `/movies/genre/<int:genre_pk>/` | Listado de las películas de un género |

El prefijo `genre/` es necesario: una ruta desnuda `<int:genre_pk>/` sería
indistinguible de `<int:pk>/` y Django mandaría toda URL de película a la vista que
se declarara primero.

## Autoescaping

Django escapa automáticamente el contenido que llega de la base de datos. Una
entrada como:

```html
<script>alert("xss")</script>
```

introducida en `Rating.comment`, `Genre.description`, `Genre.name` o `Movie.title`
se publica como texto inerte:

```html
<p>&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;</p>
```

El visitante sigue leyendo el texto, pero no se crea ninguna etiqueta ejecutable.
Ninguna plantilla del proyecto usa `|safe`, `|safeseq`, `|safejs`, `{% autoescape off %}`
ni `mark_safe`.

Está verificado por pruebas en `movies/tests.py`: analizan el HTML publicado con un
parser y fallan si aparece una etiqueta `<script>` o un atributo inyectado, y
comprueban también que el texto visible se conserva.

## Administración

El contenido se gestiona desde el Django Admin en `/admin/`. Para entrar hace falta
crear un superusuario:

```bash
python manage.py createsuperuser
```

No hay usuarios ni credenciales en el repositorio.

Las cuatro entidades están registradas:

- **Genre** (`/admin/movies/genre/`) — listado con nombre, descripción y número de
  películas; búsqueda por nombre o descripción; filtro por si tiene películas o no.
- **Person** (`/admin/movies/person/`) — listado con nombre, fecha de nacimiento y
  número de películas dirigidas; búsqueda por nombre o biografía; filtro por si ha
  dirigido alguna película. No se puede borrar una persona que dirige películas
  (`on_delete=PROTECT`).
- **Movie** (`/admin/movies/movie/`) — listado con título, año, director y puntuación
  media calculada; filtros por género y por año; búsqueda por título o descripción;
  selección múltiple de géneros y director con autocompletado; y las valoraciones se
  editan desde la propia ficha mediante un inline.
- **Rating** (`/admin/movies/rating/`) — listado con película, puntuación y
  comentario; filtro por puntuación; búsqueda por título de película o comentario;
  y película con autocompletado.

Lo registrado en el Admin aparece de inmediato en el catálogo, en el listado del
género y en la ficha, con la puntuación media recalculada.

## Pruebas

```bash
python manage.py test
```

**102 tests en verde.** Cubren vistas y códigos de respuesta, plantillas y
herencia, relaciones entre modelos, navegación y rutas, el fragmento de tarjeta
reutilizado en sus tres usos, estados vacíos, estadísticas de valoración, búsqueda
y filtros del catálogo, el escapado automático del contenido de la base de datos, y
la ausencia de HTML duplicado fuera del fragmento.

Las pruebas no necesitan datos previos: cada una construye los suyos en una base de
datos temporal.

## Puesta en marcha

Crear y activar un entorno virtual:

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS / Linux
```

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

Opcionalmente definir una clave de firma (el proyecto tiene un valor de desarrollo
para funcionar sin configurarla):

```bash
DJANGO_SECRET_KEY=your-secret-key
```

Aplicar las migraciones y arrancar el servidor:

```bash
python manage.py migrate
python manage.py runserver
```

El catálogo queda en http://127.0.0.1:8000/movies/ y el Admin en
http://127.0.0.1:8000/admin/.

## Notas de configuración

- `ALLOWED_HOSTS` está limitado a los hosts locales (`localhost`, `127.0.0.1`,
  `[::1]`) y hay que ampliarlo antes de cualquier despliegue.
- `SECRET_KEY` se lee de la variable de entorno `DJANGO_SECRET_KEY`. Sin ella se usa
  un valor de desarrollo y `DEBUG` está activo; ambos deben cambiarse en producción.
- Los archivos estáticos los sirve `runserver` mientras `DEBUG` sea `True`; para
  reunirlos hay que ejecutar `python manage.py collectstatic`.
- Los archivos subidos por los usuarios sólo los sirve Django mientras `DEBUG` sea
  `True`. En producción deberían servirlos directamente el servidor web.