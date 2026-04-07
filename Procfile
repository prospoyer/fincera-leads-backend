web: mkdir -p /data && python -m django migrate --run-syncdb && python -m gunicorn fincera_project.wsgi --bind 0.0.0.0:$PORT --workers 2
