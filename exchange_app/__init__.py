import logging
import os
from flask import Flask
from flask_redis import FlaskRedis
from flask_pymongo import PyMongo
import requests

FLASK_APP_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__
)

# Config
app.config.from_object('exchange_app.settings.app_config')
app.logger.info("Config: %s" % app.config['ENVIRONMENT'])

# Logging
logging.basicConfig(
    level=app.config['LOG_LEVEL'],
    format='%(asctime)s %(levelname)s: %(message)s '
           '[in %(pathname)s:%(lineno)d]',
    datefmt='%Y%m%d-%H:%M%p',
)

#Session
app.lykke_session = requests.Session()  #Used for connection pooling requests to lykke api

# Redis
redis_store = FlaskRedis(app, strict=False)

# MongoDB
mongo = PyMongo(app)

# Business Logic
from . import signservice
from . import api_1_0
from .common import api as api_blueprint
app.register_blueprint(api_blueprint, url_prefix='/v1/api')

