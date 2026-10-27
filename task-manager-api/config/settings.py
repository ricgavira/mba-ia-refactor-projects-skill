import os
import secrets


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes')


class Settings:
    """Toda configuração vem do ambiente; nenhum segredo mora no código."""

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Sem SECRET_KEY no ambiente, gera uma chave efêmera (tokens não sobrevivem ao restart).
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DEBUG = _env_bool('DEBUG', False)
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', '5000'))

    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USER = os.environ.get('EMAIL_USER', '')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
