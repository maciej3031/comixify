#!/bin/sh

start (){
    gunicorn --bind :8080 settings.wsgi:application
}

migrate (){
    python3 manage.py migrate --noinput
}

collectstatic (){
    python3 manage.py collectstatic --clear --no-input
}

migrate
collectstatic
start
