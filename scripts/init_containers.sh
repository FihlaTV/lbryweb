#!/bin/bash

docker-compose build
echo "Creating db container"
docker-compose up -d db
docker-compose start db
echo "Waiting for db"
while ! curl -S localhost:5432 2>&1 | grep 52; do echo "Waiting for db" && sleep 1; done
echo "Resetting the database"
docker-compose run app pipenv run python manage.py reset_db --noinput
echo "Running migrations"
docker-compose run app pipenv run python manage.py migrate
docker-compose up
