from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config, FLASK_ENV

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=config[FLASK_ENV]):
    """Create the main app"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .models import User

    return app
