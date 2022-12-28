./wait-for-it.sh mysql:3306 -- python manage.py migrate
gunicorn --bind=0.0.0.0 qimeng.wsgi