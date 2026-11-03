import logging

from flask import jsonify, request

from config.constants import DEFAULT_ROLE
from database import commit, db
from errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from middlewares.auth import current_user, is_admin_request, require_admin
from models.task import Task
from models.user import User
from services.token_service import generate_token
from utils.validators import (
    require_json_object,
    validate_email_field,
    validate_password_field,
    validate_role_field,
)

logger = logging.getLogger(__name__)


def _get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def _ensure_email_available(email, ignore_user_id=None):
    existing = User.find_by_email(email)
    if existing and existing.id != ignore_user_id:
        raise ConflictError('Email já cadastrado')


def list_users():
    task_counts = Task.count_by(Task.user_id)  # uma query agrupada em vez de len(u.tasks) por usuário
    result = []
    for user in User.list_all():
        data = user.to_dict()
        data['task_count'] = task_counts.get(user.id, 0)
        result.append(data)
    return jsonify(result), 200


def get_user(user_id):
    user = _get_user_or_404(user_id)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Task.list_by_user(user_id)]
    return jsonify(data), 200


def create_user():
    data = require_json_object(request.get_json(silent=True))
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    # Cadastro público: o role enviado só vale para um admin autenticado; para anônimos é ignorado.
    role = data.get('role', DEFAULT_ROLE) if is_admin_request() else DEFAULT_ROLE

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    validate_email_field(email)
    validate_password_field(password, 'Senha deve ter no mínimo 4 caracteres')
    _ensure_email_available(email)
    validate_role_field(role)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    commit()
    logger.info('Usuário criado: %s - %s', user.id, user.name)
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    user = _get_user_or_404(user_id)
    data = require_json_object(request.get_json(silent=True))
    if ('role' in data or 'active' in data) and not is_admin_request():
        # papel e status só podem ser alterados por um admin autenticado
        if current_user() is None:
            raise UnauthorizedError('Autenticação necessária')
        raise ForbiddenError('Acesso restrito a administradores')

    if 'name' in data:
        if not isinstance(data['name'], str) or not data['name']:
            raise ValidationError('Nome inválido')
        user.name = data['name']
    if 'email' in data:
        validate_email_field(data['email'])
        _ensure_email_available(data['email'], ignore_user_id=user_id)
        user.email = data['email']
    if 'password' in data:
        validate_password_field(data['password'], 'Senha muito curta')
        user.set_password(data['password'])
    if 'role' in data:
        validate_role_field(data['role'])
        user.role = data['role']
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Campo active deve ser booleano')
        user.active = data['active']

    commit()
    return jsonify(user.to_dict()), 200


@require_admin
def delete_user(user_id):
    user = _get_user_or_404(user_id)
    for task in Task.list_by_user(user_id):  # tasks do usuário são removidas junto, na mesma transação
        db.session.delete(task)
    db.session.delete(user)
    commit()
    logger.info('Usuário deletado: %s', user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def list_user_tasks(user_id):
    _get_user_or_404(user_id)
    return jsonify([task.to_summary_dict() for task in Task.list_by_user(user_id)]), 200


def login():
    data = require_json_object(request.get_json(silent=True))
    email, password = data.get('email'), data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    if not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Email e senha devem ser texto')

    user = User.find_by_email(email)
    if not user or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': generate_token(user),
    }), 200
