#!/bin/bash

docker-compose build
docker-compose run app pipenv run python lbryweb/manage.py reset_db --noinput
docker-compose run app pipenv run python lbryweb/manage.py migrate
docker-compose up
