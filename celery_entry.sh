redis-server&
flask run&
sleep 3
celery -A monolith.app.celery worker -l info&
celery -A monolith.app.celery beat -l info