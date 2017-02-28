from flask import Flask
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config

bootstrap = Bootstrap()
moment = Moment()
db = SQLAlchemy()


def create_app(config_name):
    financial_instability_app = Flask(__name__)
    financial_instability_app.config.from_object(config[config_name])
    config[config_name].init_app(financial_instability_app)

    bootstrap.init_app(financial_instability_app)
    moment.init_app(financial_instability_app)
    db.init_app(financial_instability_app)

    from .main import main as main_blueprint
    financial_instability_app.register_blueprint(main_blueprint)

    return financial_instability_app
