"""Mapeamento URL → controller. Nenhuma lógica aqui."""
from flask import Blueprint

from controllers import system_controller

system_bp = Blueprint('system', __name__)

system_bp.add_url_rule('/health', 'health', system_controller.health, methods=['GET'])
system_bp.add_url_rule('/', 'index', system_controller.index, methods=['GET'])
