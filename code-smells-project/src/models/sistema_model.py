from flask import current_app

from src.database.connection import connect_readonly, get_db, transaction
from src.errors import ValidationError

TABELAS_CONTADAS = ("produtos", "usuarios", "pedidos")
TABELAS_RESETAVEIS = ("itens_pedido", "pedidos", "produtos", "usuarios")  # ordem respeita dependências


def contar_registros():
    db = get_db()
    # nomes de tabela vêm da constante acima, nunca do cliente
    return {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABELAS_CONTADAS}


def resetar_banco():
    with transaction() as db:
        for tabela in TABELAS_RESETAVEIS:
            db.execute(f"DELETE FROM {tabela}")


def executar_select(sql):
    """Executa uma consulta SELECT em conexão somente-leitura."""
    if not sql.lstrip().lower().startswith("select"):
        raise ValidationError("Apenas consultas SELECT são permitidas")
    conn = connect_readonly(current_app.config["DB_PATH"])
    try:
        return [dict(row) for row in conn.execute(sql).fetchall()]
    except Exception as exc:
        raise ValidationError(f"Consulta inválida: {exc}") from exc
    finally:
        conn.close()
