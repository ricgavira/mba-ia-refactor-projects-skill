import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({'error': err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        # o detalhe fica no log; o cliente recebe uma mensagem genérica
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
