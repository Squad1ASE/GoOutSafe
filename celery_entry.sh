#!/bin/sh

flask run&
celery -A monolith.app.celery worker -l info&
celery -A monolith.app.celery beat -l info
