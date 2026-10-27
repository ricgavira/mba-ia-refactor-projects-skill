from src.config.constants import STATUS_PEDIDO_INICIAL
from src.database.connection import get_db, transaction
from src.errors import ValidationError

CAMPOS_PEDIDO = ("id", "usuario_id", "status", "total", "criado_em")

_SQL_PEDIDOS_COM_ITENS = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    {filtro}
    ORDER BY p.id, i.id
"""


def _agrupar(rows):
    """Transforma as linhas do JOIN em pedidos com a lista de itens aninhada."""
    pedidos = {}
    for row in rows:
        pedido = pedidos.setdefault(
            row["id"], {**{campo: row[campo] for campo in CAMPOS_PEDIDO}, "itens": []}
        )
        if row["produto_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def listar_todos():
    rows = get_db().execute(_SQL_PEDIDOS_COM_ITENS.format(filtro="")).fetchall()
    return _agrupar(rows)


def listar_por_usuario(usuario_id):
    sql = _SQL_PEDIDOS_COM_ITENS.format(filtro="WHERE p.usuario_id = ?")
    return _agrupar(get_db().execute(sql, (usuario_id,)).fetchall())


def criar(usuario_id, itens):
    """Cria o pedido, os itens e baixa o estoque em uma única transação."""
    with transaction() as db:
        total = 0
        precos = {}
        for item in itens:
            produto = db.execute(
                "SELECT nome, preco, estoque FROM produtos WHERE id = ?", (item["produto_id"],)
            ).fetchone()
            if produto is None:
                raise ValidationError(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
            precos[item["produto_id"]] = produto["preco"]
            total += produto["preco"] * item["quantidade"]

        pedido_id = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PEDIDO_INICIAL, total),
        ).lastrowid

        for item in itens:
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], precos[item["produto_id"]]),
            )
            db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
    return {"pedido_id": pedido_id, "total": total}


def existe(pedido_id):
    return get_db().execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None


def atualizar_status(pedido_id, novo_status):
    get_db().execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
