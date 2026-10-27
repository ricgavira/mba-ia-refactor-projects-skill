import logging

from flask import jsonify, request

from src.config.constants import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
)
from src.errors import NotFoundError, ValidationError
from src.models import produto_model

logger = logging.getLogger(__name__)


def _numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _validar_produto(dados):
    """Validação única usada em criação e atualização."""
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    for campo, rotulo in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
        if campo not in dados:
            raise ValidationError(f"{rotulo} é obrigatório")

    nome, preco, estoque = dados["nome"], dados["preco"], dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if not _numero(preco):
        raise ValidationError("Preço inválido")
    if not _numero(estoque):
        raise ValidationError("Estoque inválido")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError(f"Categoria inválida. Válidas: {list(CATEGORIAS_VALIDAS)}")

    return nome, dados.get("descricao", ""), preco, estoque, categoria


def _obter_ou_404(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return produto


def _preco_query(nome):
    valor = request.args.get(nome)
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"Parâmetro {nome} inválido")


def listar_produtos():
    produtos = produto_model.listar_todos()
    logger.info("Listando %s produtos", len(produtos))
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id):
    return jsonify({"dados": _obter_ou_404(id), "sucesso": True}), 200


def criar_produto():
    campos = _validar_produto(request.get_json(silent=True))
    produto_id = produto_model.criar(*campos)
    logger.info("Produto criado com ID: %s", produto_id)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    _obter_ou_404(id)
    campos = _validar_produto(request.get_json(silent=True))
    produto_model.atualizar(id, *campos)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    _obter_ou_404(id)
    produto_model.deletar(id)
    logger.info("Produto %s deletado", id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    resultados = produto_model.buscar(
        termo=request.args.get("q", ""),
        categoria=request.args.get("categoria"),
        preco_min=_preco_query("preco_min"),
        preco_max=_preco_query("preco_max"),
    )
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
