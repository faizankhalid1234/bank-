release: sh -c "cd backend && python manage.py migrate --noinput"
web: sh -c "cd backend && gunicorn alybank.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120"
