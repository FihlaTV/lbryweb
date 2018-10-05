# LBRY Web

<!-- [![CircleCI](https://img.shields.io/circleci/project/lbryio/lbryweb.svg)](https://circleci.com/gh/lbryio/lbryweb/tree/master) [![Coverage](https://img.shields.io/coveralls/github/lbryio/lbryweb.svg)](https://coveralls.io/github/lbryio/lbryweb) -->

## Installation

Python 3.7 is recommended and specified as a target in `Pipfile`. Install pipenv, let it install project dependencies and launch pipenv shell:

```
pipenv install --dev
pipenv shell
```

Now you can load sample data and launch the application.

```
cd lbryweb
./manage.py migrate
./manage.py runserver
```

The installation is done and the application is exposed on http://127.0.0.1:8000/.


## Running tests

For running tests on local machine, you need docker containers `db` and `daemon_test_local` up and running.

```
docker-compose up db daemon_test_local
```

Tests are launched using pytest:

`pytest`

Supply `--cov` argument to get test coverage:

`pytest --cov=lbryweb`

## Code quality

Run `flake8` and/or configure your editor to use it to validate the code against the project style rules.

Visit [Django Coding style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/) for additional guidance.
