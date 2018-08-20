#!/bin/sh

start (){
    gunicorn --bind :8080 settings.wsgi:application --timeout 300
}

migrate (){
    python3.6 manage.py migrate --noinput
}

collectstatic (){
    python3.6 manage.py collectstatic --clear --no-input
}

migrate
collectstatic
start
