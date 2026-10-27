from src.database.connection import get_db

CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _para_dict(row):
    return {campo: row[campo] for campo in CAMPOS}


def listar_todos():
    rows = get_db().execute("SELECT * FROM produtos").fetchall()
    return [_para_dict(row) for row in rows]


def buscar_por_id(produto_id):
    row = get_db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return _para_dict(row) if row else None


def buscar(termo="", categoria=None, preco_min=None, preco_max=None):
    clausulas, params = ["1=1"], []
    if termo:
        clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        clausulas.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        clausulas.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        clausulas.append("preco <= ?")
        params.append(preco_max)

    rows = get_db().execute(
        "SELECT * FROM produtos WHERE " + " AND ".join(clausulas), params
    ).fetchall()
    return [_para_dict(row) for row in rows]


def criar(nome, descricao, preco, estoque, categoria):
    cursor = get_db().execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    return cursor.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    get_db().execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )


def deletar(produto_id):
    get_db().execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
