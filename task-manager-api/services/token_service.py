from flask import current_app
from itsdangerous import URLSafeTimedSerializer

_SALT = 'task-manager-auth'


def generate_token(user):
    """Token assinado com a SECRET_KEY (substitui o antigo 'fake-jwt-token-<id>', forjável por qualquer um).

    A verificação do token nas rotas ainda não é exigida: ver "risco residual" no relatório de auditoria.
    """
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=_SALT).dumps({'user_id': user.id})
