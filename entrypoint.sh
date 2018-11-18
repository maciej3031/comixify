#!/bin/sh

start (){
    gunicorn --bind :8008 settings.wsgi:application --timeout 300 --workers 2
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
