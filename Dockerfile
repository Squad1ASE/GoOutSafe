FROM ubuntu:20.04

RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential
RUN apt install -y redis-server

ADD . /app
WORKDIR /app

RUN pip3 install -r requirements.txt
RUN python3 setup.py develop


EXPOSE 5000

#CMD ["flask", "run"]
