FROM python:3.7-alpine

RUN apk update && \
    apk upgrade && \
    apk add postgresql-dev python-dev py-pip build-base libffi-dev openssl-dev libgcc py-mysqldb

WORKDIR /app

ADD requirements.txt /app

RUN pip install -r requirements.txt

ADD . /app

EXPOSE 5000

CMD [ "python", "./manage.py", "run"]