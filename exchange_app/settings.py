import logging

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = True
    TESTING = False
    PRODUCTION = False

    SECRET_KEY = '1!qaz2@wsx3#edc$4rfv'
    WTF_CSRF_SECRET_KEY = '1!qaz2@wsx3#edc$4rfv'
    SITE_NAME = ''
    LOG_LEVEL = logging.DEBUG
    SERVER_NAME = 'localhost:5000'
    #: Database
    MONGO_DBNAME = 'LYKKE'
    MONGO_HOST = '127.0.0.1'
    MONGO_PORT = 27017
    #: Redis
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    #: SKYCOIN
    SKYCOIN_NODE_URL = 'http://localhost:6420/api/v1'


class ProductionConfig(Config):
    ENVIRONMENT = 'Production'
    PRODUCTION = True
    LOG_LEVEL = logging.INFO
    SERVER_NAME = ''


class DevelopmentConfig(Config):
    ENVIRONMENT = 'Dev'
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    ENVIRONMENT = 'Testing'
    DEBUG = False
    TESTING = True


environment = os.getenv('ENVIRONMENT', 'DEVELOPMENT').lower()

if environment == 'testing':
    app_config = TestingConfig()
elif environment == 'production':
    app_config = ProductionConfig()
else:
    app_config = DevelopmentConfig()
