import logging

from flask import jsonify, request

from config.constants import DEFAULT_PRIORITY, DEFAULT_STATUS
from database import commit, db
from errors import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage, utc_now
from utils.validators import validate_task_payload

logger = logging.getLogger(__name__)


def _get_task_or_404(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def _check_relations(fields):
    """Garante que user_id/category_id informados existem (404 caso contrário)."""
    if fields.get('user_id') and not db.session.get(User, fields['user_id']):
        raise NotFoundError('Usuário não encontrado')
    if fields.get('category_id') and not db.session.get(Category, fields['category_id']):
        raise NotFoundError('Categoria não encontrada')


def _optional_int_arg(name):
    value = request.args.get(name, '')
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(f'Parâmetro {name} inválido')


def list_tasks():
    tasks = Task.list_all(with_relations=True)
    return jsonify([t.to_dict(include_overdue=True, include_relations=True) for t in tasks]), 200


def get_task(task_id):
    task = _get_task_or_404(task_id)
    return jsonify(task.to_dict(include_overdue=True)), 200


def create_task():
    fields = validate_task_payload(request.get_json(silent=True), require_title=True)
    fields.setdefault('description', '')
    fields.setdefault('status', DEFAULT_STATUS)
    fields.setdefault('priority', DEFAULT_PRIORITY)
    fields['tags'] = fields.get('tags') or None
    _check_relations(fields)

    task = Task(**fields)
    db.session.add(task)
    commit()
    logger.info('Task criada: %s - %s', task.id, task.title)
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = _get_task_or_404(task_id)
    fields = validate_task_payload(request.get_json(silent=True), require_title=False)
    _check_relations(fields)

    for key, value in fields.items():
        setattr(task, key, value)
    task.updated_at = utc_now()
    commit()
    logger.info('Task atualizada: %s', task.id)
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    task = _get_task_or_404(task_id)
    db.session.delete(task)
    commit()
    logger.info('Task deletada: %s', task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    tasks = Task.search(
        query=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=_optional_int_arg('priority'),
        user_id=_optional_int_arg('user_id'),
    )
    return jsonify([t.to_dict() for t in tasks]), 200


def task_stats():
    by_status = Task.count_by(Task.status)
    total = sum(by_status.values())
    done = by_status.get('done', 0)
    return jsonify({
        'total': total,
        'pending': by_status.get('pending', 0),
        'in_progress': by_status.get('in_progress', 0),
        'done': done,
        'cancelled': by_status.get('cancelled', 0),
        'overdue': Task.count_overdue(),
        'completion_rate': calculate_percentage(done, total),
    }), 200
