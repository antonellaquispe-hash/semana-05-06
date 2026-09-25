# DAE — Movie Management System

Django project for a movie management system.

## Requirements

- Python 3.12+
- Django 5.2
- Pillow (required for `ImageField` support)

## Project layout

```
DAE/
├── manage.py               # Django command-line utility
├── requirements.txt        # Python dependencies
├── DAE/                    # Project configuration package
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── movies/                 # Movie application
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── static/                 # Project-level static files
├── media/                  # User-uploaded media files
└── db.sqlite3              # Development database (generated)
```

## Getting started

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS / Linux
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Apply the migrations:

```bash
python manage.py migrate
```

Run the development server:

```bash
python manage.py runserver
```

The site is then available at http://127.0.0.1:8000/ and the admin at
http://127.0.0.1:8000/admin/.

## Configuration notes

- `ALLOWED_HOSTS` is limited to the local development hosts (`localhost`,
  `127.0.0.1`, `[::1]`) and must be extended before any deployment.
- `SECRET_KEY` and `DEBUG` hold development values and must be replaced for
  production.
- Static files are served by `runserver` while `DEBUG` is `True`; run
  `python manage.py collectstatic` to gather them into `STATIC_ROOT`.
- User-uploaded media files are served by Django only while `DEBUG` is `True`.
  In production they should be served directly by the web server.
