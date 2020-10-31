FROM python:3.8-alpine

ADD . /app
WORKDIR /app

RUN pip install -r requirements.txt

#ENV FLASK_RUN_HOST 0.0.0.0
#ENV FLASK_APP monolith/app.py
#ENV PYTHONPATH "/app"

EXPOSE 5000

#CMD ["flask", "run"]
