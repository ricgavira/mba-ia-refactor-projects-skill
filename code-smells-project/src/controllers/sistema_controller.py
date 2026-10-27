import logging

from flask import jsonify, request

from src.config.constants import APP_VERSION
from src.errors import ValidationError
from src.models import sistema_model

logger = logging.getLogger(__name__)


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": APP_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


def health_check():
    # Apenas status e contagens: nada de segredo, caminho ou flag de debug.
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": sistema_model.contar_registros(),
        "versao": APP_VERSION,
    }), 200


def reset_database():
    sistema_model.resetar_banco()
    logger.warning("Banco de dados resetado via /admin/reset-db")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    dados = request.get_json(silent=True)
    query = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not query or not isinstance(query, str):
        raise ValidationError("Query não informada")
    return jsonify({"dados": sistema_model.executar_select(query), "sucesso": True}), 200
