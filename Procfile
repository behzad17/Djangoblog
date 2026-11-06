release: python manage.py migrate --noinput
web: gunicorn codestar.wsgi:application --log-file - --access-logfile - --error-logfile - --capture-output --timeout 120
