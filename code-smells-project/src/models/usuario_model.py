from werkzeug.security import check_password_hash, generate_password_hash

from src.config.constants import TIPO_USUARIO_PADRAO
from src.database.connection import get_db

# Allowlist de campos expostos: a senha (hash) nunca sai do model.
CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")


def _para_dict(row):
    return {campo: row[campo] for campo in CAMPOS_PUBLICOS}


def listar_todos():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_para_dict(row) for row in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _para_dict(row) if row else None


def autenticar(email, senha):
    """Retorna o usuário (sem senha) se as credenciais forem válidas, senão None."""
    row = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row and check_password_hash(row["senha"], senha):
        return {campo: row[campo] for campo in ("id", "nome", "email", "tipo")}
    return None


def criar(nome, email, senha, tipo=TIPO_USUARIO_PADRAO):
    cursor = get_db().execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, generate_password_hash(senha), tipo),
    )
    return cursor.lastrowid
