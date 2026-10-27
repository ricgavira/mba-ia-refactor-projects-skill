from flask import jsonify

from database import db
from errors import NotFoundError
from models.user import User
from services import report_service


def summary_report():
    return jsonify(report_service.summary_report()), 200


def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return jsonify(report_service.user_report(user)), 200
