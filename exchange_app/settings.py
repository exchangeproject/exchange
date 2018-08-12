import logging
import uuid
import os
import os.path

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = True
    TESTING = False
    PRODUCTION = False
    SECRET_KEY = '1!qaz2@wsx3#edc$4rfv'
    WTF_CSRF_SECRET_KEY = '1!qaz2@wsx3#edc$4rfv'


class ProductionConfig(Config):
    ENVIRONMENT = 'Production'
    PRODUCTION = True
    LOG_LEVEL = logging.INFO
    #: Site Name
    SITE_NAME = ''
    SERVER_NAME = ''
    #: Database
    MONGO_DBNAME = ''
    MONGO_HOST = ''
    MONGO_PORT = 27017
    MONGO_URI = "mongodb://"
    #: Redis
    REDIS_HOST = ''
    REDIS_PORT = 6379
    #: SKYCOIN
    SKYCOIN_NODE_URL = ''


class DevelopmentConfig(Config):
    ENVIRONMENT = 'Dev'
    DEBUG = True
    TESTING = False
    LOG_LEVEL = logging.DEBUG
    #: Site Name
    SITE_NAME = ''
    SERVER_NAME = 'localhost:5000'
    #: Database
    MONGO_DBNAME = 'LYKKE'
    MONGO_HOST = '127.0.0.1'
    MONGO_PORT = 27017
    MONGO_URI = "mongodb://" + MONGO_HOST + ":" + str(MONGO_PORT) + "/" + MONGO_DBNAME
    #: Redis
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    #: SKYCOIN
    SKYCOIN_NODE_URL = 'http://localhost:6420/'


class TestingConfig(Config):
    ENVIRONMENT = 'Testing'
    DEBUG = False
    TESTING = True
    LOG_LEVEL = logging.DEBUG
    #: Site Name
    SITE_NAME = ''
    SERVER_NAME = 'localhost:5000'
    #: Database
    MONGO_DBNAME = 'LYKKE_TEST_{0}'.format(str(uuid.uuid1()).replace('-', ''))
    MONGO_HOST = '127.0.0.1'
    MONGO_PORT = 27017
    MONGO_URI = "mongodb://" + MONGO_HOST + ":" + str(MONGO_PORT) + "/" + MONGO_DBNAME
    #: Redis
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    #: SKYCOIN
    SKYCOIN_NODE_URL = 'http://localhost:6420/'


environment = os.getenv('ENVIRONMENT', 'DEVELOPMENT').lower()

if environment == 'testing':
    app_config = TestingConfig()
elif environment == 'production':
    app_config = ProductionConfig()
else:
    app_config = DevelopmentConfig()
