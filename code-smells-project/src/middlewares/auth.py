import hmac
from functools import wraps

from flask import current_app, request

from src.errors import ForbiddenError


def require_admin_token(view):
    """Protege rotas administrativas com o header X-Admin-Token.

    Se ADMIN_TOKEN não estiver configurado, as rotas ficam desabilitadas (403).
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        esperado = current_app.config.get("ADMIN_TOKEN")
        recebido = request.headers.get("X-Admin-Token", "")
        if not esperado or not hmac.compare_digest(recebido, esperado):
            raise ForbiddenError("Acesso negado")
        return view(*args, **kwargs)

    return wrapper
