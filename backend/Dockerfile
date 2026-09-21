FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# The backend depends on the local, framework-agnostic `agent` package.
# Layout mirrors the repo root so `-e ..` in requirements.txt resolves correctly.
COPY pyproject.toml ./pyproject.toml
COPY agent ./agent
COPY backend ./backend

RUN pip install --no-cache-dir -e . -r backend/requirements.txt

WORKDIR /app/backend

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
