# syntax=docker/dockerfile:1
# Build React SPA, then run Django + Gunicorn (migrations on start).

FROM node:20-alpine AS spa
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

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

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=spa /static/spa ./static/spa

RUN python manage.py collectstatic --noinput --clear

EXPOSE 8000

CMD sh -c "python manage.py migrate --noinput && exec gunicorn alybank.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120"
