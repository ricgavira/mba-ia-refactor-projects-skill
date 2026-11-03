from flask import current_app
from itsdangerous import BadSignature, URLSafeTimedSerializer

_SALT = 'task-manager-auth'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=_SALT)


def generate_token(user):
    """Token assinado com a SECRET_KEY (substitui o antigo 'fake-jwt-token-<id>', forjável por qualquer um)."""
    return _serializer().dumps({'user_id': user.id})


def verify_token(token):
    """Devolve o user_id do token, ou None se a assinatura for inválida ou o token estiver expirado."""
    try:
        payload = _serializer().loads(token, max_age=current_app.config['TOKEN_MAX_AGE_SECONDS'])
    except BadSignature:  # inclui SignatureExpired
        return None
    return payload.get('user_id')
