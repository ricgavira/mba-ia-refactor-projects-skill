from flask import jsonify, request

from src.config.constants import STATUS_PEDIDO
from src.errors import NotFoundError, ValidationError
from src.models import pedido_model
from src.services import notificacao_service


def _inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _validar_itens(itens):
    if not itens or not isinstance(itens, list):
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if not isinstance(item, dict) or not _inteiro(item.get("produto_id")) \
                or not _inteiro(item.get("quantidade")) or item["quantidade"] <= 0:
            raise ValidationError("Cada item deve ter produto_id e quantidade (inteiro > 0)")


def criar_pedido():
    dados = request.get_json(silent=True)
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    itens = dados.get("itens", [])
    _validar_itens(itens)

    resultado = pedido_model.criar(usuario_id, itens)
    notificacao_service.pedido_criado(resultado["pedido_id"], usuario_id)

    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso",
    }), 201


def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": pedido_model.listar_por_usuario(usuario_id), "sucesso": True}), 200


def listar_todos_pedidos():
    return jsonify({"dados": pedido_model.listar_todos(), "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_PEDIDO:
        raise ValidationError("Status inválido")
    if not pedido_model.existe(pedido_id):
        raise NotFoundError("Pedido não encontrado")

    pedido_model.atualizar_status(pedido_id, novo_status)
    notificacao_service.status_pedido_alterado(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
