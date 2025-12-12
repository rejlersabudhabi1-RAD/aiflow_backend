# AIFlow Backend

Django REST Framework backend for AIFlow application.

## Features

- Django 5.0 with REST Framework
- PostgreSQL database (Railway)
- Redis for caching and Celery
- Celery for async tasks
- JWT Authentication
- OpenAI integration
- Swagger/OpenAPI documentation
- CORS configured
- WhiteNoise for static files

## Quick Start

### Local Development

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create .env file:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run migrations:**
```bash
python manage.py migrate
```

5. **Create superuser:**
```bash
python manage.py createsuperuser
```

6. **Run development server:**
```bash
python manage.py runserver
```

7. **Run Celery worker (in separate terminal):**
```bash
celery -A config worker -l info
```

8. **Run Celery beat (in separate terminal):**
```bash
celery -A config beat -l info
```

## API Documentation

- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- ReDoc: `http://localhost:8000/api/schema/redoc/`
- Health Check: `http://localhost:8000/api/v1/health/`

## Environment Variables

See `.env.example` for required environment variables:

- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - Database config
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` - Redis config
- `OPENAI_API_KEY` - OpenAI API key
- `CORS_ALLOWED_ORIGINS` - Allowed frontend origins

## Deployment

See [DEPLOYMENT.md](../DEPLOYMENT.md) for Railway deployment instructions.

## Project Structure

```
backend/
├── apps/
│   ├── core/         # Base models and utilities
│   ├── users/        # User management
│   └── api/          # API endpoints
├── config/           # Django settings and configuration
├── media/            # User uploaded files
├── staticfiles/      # Collected static files
├── manage.py         # Django management script
├── requirements.txt  # Python dependencies
├── Procfile          # Railway/Heroku process file
├── railway.json      # Railway configuration
└── runtime.txt       # Python version specification
```

## Technologies

- **Framework:** Django 5.0, Django REST Framework 3.14
- **Database:** PostgreSQL 16
- **Cache/Broker:** Redis 7
- **Task Queue:** Celery 5.3
- **WSGI Server:** Gunicorn 21.2
- **Authentication:** SimpleJWT
- **API Docs:** drf-spectacular
- **AI:** OpenAI API

## Development

```bash
# Run tests
python manage.py test

# Create new app
python manage.py startapp app_name

# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Create superuser
python manage.py createsuperuser
```

## License

MIT
