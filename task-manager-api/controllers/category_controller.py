from flask import jsonify, request

from config.constants import DEFAULT_COLOR
from database import commit, db
from errors import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from utils.validators import require_json_object, validate_color_field


def _get_category_or_404(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_categories():
    task_counts = Task.count_by(Task.category_id)  # uma query agrupada em vez de count() por categoria
    result = []
    for category in Category.list_all():
        data = category.to_dict()
        data['task_count'] = task_counts.get(category.id, 0)
        result.append(data)
    return jsonify(result), 200


def create_category():
    data = require_json_object(request.get_json(silent=True))
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')
    color = data.get('color', DEFAULT_COLOR)
    validate_color_field(color)

    category = Category(name=name, description=data.get('description', ''), color=color)
    db.session.add(category)
    commit()
    return jsonify(category.to_dict()), 201


def update_category(category_id):
    category = _get_category_or_404(category_id)
    data = require_json_object(request.get_json(silent=True))

    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        validate_color_field(data['color'])
        category.color = data['color']

    commit()
    return jsonify(category.to_dict()), 200


def delete_category(category_id):
    category = _get_category_or_404(category_id)
    # integridade referencial: as tasks da categoria ficam sem categoria, não com id órfão
    for task in db.session.execute(db.select(Task).where(Task.category_id == category_id)).scalars():
        task.category_id = None
    db.session.delete(category)
    commit()
    return jsonify({'message': 'Categoria deletada'}), 200
