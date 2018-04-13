# exchange project

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
```

### Adding or improving features

Create a branch with the feature's name

```bash
git checkout -b new_feature
```

### Technologies and stacks

1. flask
2. flask-redis
3. flask-restful
4. flask-pymongo



