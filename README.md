[![Build Status](https://travis-ci.com/exchangeproject/exchange.svg?branch=develop)](https://travis-ci.com/exchangeproject/exchange)

# Lykke Blockchain integration for Skycoin

- [Python](http://www.python.org) >= 3.4 , tested with versions `3.4` , `3.5` , `3.6`
- [MongoDB](https://www.mongodb.com/) tested with version `3.6.4`
- [Redis](https://redis.io/) tested with version `3.0.7`

### Installation

In order to run **exchange project** during development you need to do:

Install dependencies on local machine(Fedora example):

```bash
dnf install redis mongodb
```

Clone the repo:

```bash
git clone https://github.com/exchangeproject/exchange
cd exchange
```

Install dependencies, optionally within a virtualenv

Using virtualenvwrapper:

```bash
mkvirtualenv --no-site-packages exchange
workon exchange
pip install -r requirements.txt
```

Or this way(preferred in my case):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running

Ensure that mongodb-server is up and running

```bash
systemctl start mongod
```

Once the dependencies are installed, run the app:

For available commands, run:

```bash
python manage.py --help
```

```bash
python manage.py runserver
### Settings

Edit `settings.py` with the local settings for redis and mongodb services.

Example:

```shell
MONGOALCHEMY_DATABASE = 'exchange'
MONGOALCHEMY_SERVER = '127.0.0.1'
MONGOALCHEMY_USER = 'dev00XX'
MONGOALCHEMY_PASSWORD = 'f4cyp4assw0rd'
REDIS_URL = 'redis://localhost:6379/0'
```

### Running

Once the dependencies are installed, run the app:

```shell
python manage.py runserver
```

For available commands, run:

```shell
python manage.py runserver
```

### Testing

In order to run the tests you must install `python-nose` package

```shell
pip install nose
```
And then, you should be able to run the tests:

```shell
nosetests
```

### Adding or improving features

Create a branch with the feature's name

```bash
git checkout -b new_feature
```

### Testing

In order to run the tests you must install `python-nose` package

```shell
pip install nose
```
And then, you should be able to run the tests:

```shell
ENVIRONMENT=TESTING nosetests
```


### Technologies and stacks

1. flask
2. flask-redis
3. flask-restful
4. flask-pymongo
