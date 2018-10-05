FROM python:3.7-alpine
ENV PYTHONUNBUFFERED 1
ENV PYTHONIOENCODING utf-8
EXPOSE 8000

RUN apk update && \
 apk add postgresql-libs && \
 apk add --virtual .build-deps gcc musl-dev postgresql-dev

RUN mkdir /app
WORKDIR /app
RUN pip3 install -U pipenv
ADD Pipfile /app/
ADD Pipfile.lock /app/
RUN pipenv install 
RUN pipenv install --dev

RUN apk --purge del .build-deps
# RUN pipenv shell

# ADD ./lbryweb /app/lbryweb
WORKDIR /app/lbryweb
CMD ["pipenv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
