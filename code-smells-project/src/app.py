import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings
from src.database.connection import close_db
from src.database.schema import init_db
from src.middlewares.error_handler import register_error_handlers
from src.views.routes import api


def create_app(settings=Settings):
    """Composition root: monta configuração, banco, middlewares e rotas."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.from_object(settings)
    CORS(app)

    init_db(app.config["DB_PATH"], settings.SEED_ADMIN_PASSWORD, settings.SEED_USER_PASSWORD)
    app.teardown_appcontext(close_db)
    register_error_handlers(app)
    app.register_blueprint(api)
    return app
