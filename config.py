import os

basedir = os.path.abspath(os.path.dirname(__file__))
FLASK_ENV = os.environ.get('FLASK_ENV')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'O8HBs553>.A983)'
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT')
    DB_USER = os.environ.get('DB_USER')
    DB_NAME = os.environ.get('MYSQL_DATABASE')
    DB_PASSWORD = os.environ.get('MYSQL_ROOT_PASSWORD')
    SQLALCHEMY_DATABASE_URI = f'mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'test.db')


class ProductionConfig(Config):
    DEBUG = False

# Env configuration
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
