# syntax=docker/dockerfile:1
# Django from repo root: COPY backend → collectstatic → gunicorn. No frontend here.
# Build: docker build -t alybank-api .

FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
RUN python manage.py collectstatic --noinput --clear

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn alybank.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120"]
