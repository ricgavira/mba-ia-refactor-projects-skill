"""Mapeamento URL → controller. Nenhuma lógica aqui."""
from flask import Blueprint

from controllers import category_controller

category_bp = Blueprint('categories', __name__)

category_bp.add_url_rule('/categories', 'get_categories', category_controller.list_categories, methods=['GET'])
category_bp.add_url_rule('/categories', 'create_category', category_controller.create_category, methods=['POST'])
category_bp.add_url_rule('/categories/<int:category_id>', 'update_category',
                         category_controller.update_category, methods=['PUT'])
category_bp.add_url_rule('/categories/<int:category_id>', 'delete_category',
                         category_controller.delete_category, methods=['DELETE'])
