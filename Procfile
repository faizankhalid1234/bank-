release: python manage.py migrate --noinput
web: gunicorn alybank.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
