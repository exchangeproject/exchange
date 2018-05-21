import logging
import uuid
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


class ProductionConfig(Config):
    ENVIRONMENT = 'Production'
    PRODUCTION = True
    LOG_LEVEL = logging.INFO
    #: Server Name
    SERVER_NAME = ''
    #: Database
    MONGO_DBNAME = ''
    MONGO_HOST = ''
    MONGO_PORT = 0
    #: Redis
    REDIS_URL = "redis://localhost:6379/0"
    #: SKYCOIN
    SKYCOIN_NODE_URL = ''


class DevelopmentConfig(Config):
    ENVIRONMENT = 'Dev'
    DEBUG = True
    TESTING = False
    #: Server Name
    SERVER_NAME = 'localhost:5000'
    #: Database
    MONGO_DBNAME = 'LYKKE_DEV'
    MONGO_HOST = '127.0.0.1'
    MONGO_PORT = 27017
    #: Redis
    REDIS_URL = "redis://localhost:6379/0"
    #: SKYCOIN
    SKYCOIN_NODE_URL = 'http://localhost:6420/'


class TestingConfig(Config):
    ENVIRONMENT = 'Testing'
    DEBUG = False
    TESTING = True
    #: Server Name
    SERVER_NAME = 'localhost:5000'
    #: Database
    MONGO_DBNAME = 'LYKKE_TEST_{0}'.format(str(uuid.uuid1()).replace('-', ''))
    MONGO_HOST = '127.0.0.1'
    MONGO_PORT = 27017
    #: Redis
    REDIS_URL = "redis://localhost:6379/5"
    #: SKYCOIN
    SKYCOIN_NODE_URL = 'http://localhost:6420/'


environment = os.getenv('ENVIRONMENT', 'DEVELOPMENT').lower()

if environment == 'testing':
    app_config = TestingConfig()
elif environment == 'production':
    app_config = ProductionConfig()
else:
    app_config = DevelopmentConfig()
