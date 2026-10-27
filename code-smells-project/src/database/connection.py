import sqlite3
from contextlib import contextmanager

from flask import current_app, g


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # autocommit: transações são explícitas via transaction()
    conn.isolation_level = None
    return conn


def get_db():
    """Conexão por request (escopo de `g`), fechada em close_db."""
    if "db" not in g:
        g.db = connect(current_app.config["DB_PATH"])
    return g.db


def close_db(exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


@contextmanager
def transaction():
    """Agrupa várias escritas em uma única transação atômica."""
    conn = get_db()
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def connect_readonly(db_path):
    """Conexão somente-leitura (usada pela consulta administrativa)."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn
