import logging

from flask import jsonify, request

from src.errors import NotFoundError, UnauthorizedError, ValidationError
from src.models import usuario_model

logger = logging.getLogger(__name__)


def _corpo_json():
    dados = request.get_json(silent=True)
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    return dados


def listar_usuarios():
    return jsonify({"dados": usuario_model.listar_todos(), "sucesso": True}), 200


def buscar_usuario(id):
    usuario = usuario_model.buscar_por_id(id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    dados = _corpo_json()
    nome, email, senha = (dados.get(campo, "") for campo in ("nome", "email", "senha"))
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not all(isinstance(v, str) for v in (nome, email, senha)):
        raise ValidationError("Nome, email e senha devem ser texto")

    usuario_id = usuario_model.criar(nome, email, senha)
    logger.info("Usuário criado: %s", email)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    dados = _corpo_json()
    email, senha = dados.get("email", ""), dados.get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    if not isinstance(email, str) or not isinstance(senha, str):
        raise ValidationError("Email e senha devem ser texto")

    usuario = usuario_model.autenticar(email, senha)
    if not usuario:
        logger.info("Login falhou: %s", email)
        raise UnauthorizedError("Email ou senha inválidos")

    logger.info("Login bem-sucedido: %s", email)
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
