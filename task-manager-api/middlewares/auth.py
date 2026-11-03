from functools import wraps

from flask import request

from database import db
from errors import ForbiddenError, UnauthorizedError
from models.user import User
from services.token_service import verify_token


def current_user():
    """Usuário ativo dono do token `Authorization: Bearer <token>`, ou None se ausente/inválido."""
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    user_id = verify_token(header[len('Bearer '):].strip())
    user = db.session.get(User, user_id) if user_id else None
    return user if user and user.active else None


def is_admin_request():
    user = current_user()
    return bool(user and user.role == 'admin')


def require_admin(view):
    """401 sem token válido; 403 se o usuário autenticado não for admin."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            raise UnauthorizedError('Autenticação necessária')
        if user.role != 'admin':
            raise ForbiddenError('Acesso restrito a administradores')
        return view(*args, **kwargs)

    return wrapper
