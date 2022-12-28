python manage.py migrate
gunicorn --bind=0.0.0.0 qimeng.wsgi