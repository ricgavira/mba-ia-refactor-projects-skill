import os
import secrets


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes")


class Settings:
    """Toda configuração vem do ambiente; nenhum segredo mora no código."""

    # Sem SECRET_KEY no ambiente, gera uma chave efêmera (sessões não sobrevivem ao restart).
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _env_bool("DEBUG", False)
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    # Token dos endpoints /admin/*. Vazio = endpoints administrativos desabilitados.
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
    # Senhas dos usuários criados no seed inicial (apenas ambiente de desenvolvimento).
    SEED_ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD", "admin123")
    SEED_USER_PASSWORD = os.environ.get("SEED_USER_PASSWORD", "123456")
