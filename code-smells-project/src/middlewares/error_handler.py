import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.errors import AppError

logger = logging.getLogger(__name__)


def _erro(mensagem, status):
    return jsonify({"erro": mensagem, "sucesso": False}), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return _erro(err.message, err.status_code)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return _erro(err.description, err.code)

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        # o detalhe fica no log; o cliente recebe uma mensagem genérica
        logger.exception("Erro não tratado")
        return _erro("Erro interno do servidor", 500)
