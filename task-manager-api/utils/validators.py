"""Validação de entrada compartilhada por criação e atualização."""
from config.constants import (
    MAX_TITLE_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_TITLE_LENGTH,
    PRIORITY_MAX,
    PRIORITY_MIN,
    VALID_ROLES,
    VALID_STATUSES,
)
from errors import ValidationError
from utils.helpers import is_valid_color, parse_date, validate_email


def require_json_object(data):
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def _optional_int_id(data, key):
    value = data.get(key)
    if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
        raise ValidationError(f'{key} inválido')
    return value


def validate_task_payload(data, require_title):
    """Valida os campos presentes em `data` e devolve apenas eles, já normalizados."""
    require_json_object(data)
    cleaned = {}

    if require_title or 'title' in data:
        title = data.get('title')
        if require_title and not title:
            raise ValidationError('Título é obrigatório')
        if not isinstance(title, str):
            raise ValidationError('Título inválido')
        if len(title) < MIN_TITLE_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > MAX_TITLE_LENGTH:
            raise ValidationError('Título muito longo')
        cleaned['title'] = title

    if 'description' in data:
        if data['description'] is not None and not isinstance(data['description'], str):
            raise ValidationError('Descrição inválida')
        cleaned['description'] = data['description']

    if 'status' in data:
        if data['status'] not in VALID_STATUSES:
            raise ValidationError('Status inválido')
        cleaned['status'] = data['status']

    if 'priority' in data:
        priority = data['priority']
        if not isinstance(priority, int) or isinstance(priority, bool) \
                or not PRIORITY_MIN <= priority <= PRIORITY_MAX:
            raise ValidationError(f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}')
        cleaned['priority'] = priority

    for key in ('user_id', 'category_id'):
        if key in data:
            cleaned[key] = _optional_int_id(data, key)

    if 'due_date' in data:
        if data['due_date']:
            parsed = parse_date(data['due_date'])
            if parsed is None:
                raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')
            cleaned['due_date'] = parsed
        else:
            cleaned['due_date'] = None

    if 'tags' in data:
        tags = data['tags']
        if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
            cleaned['tags'] = ','.join(tags)
        elif tags is None or isinstance(tags, str):
            cleaned['tags'] = tags
        else:
            raise ValidationError('Tags inválidas')

    return cleaned


def validate_email_field(email):
    if not validate_email(email):
        raise ValidationError('Email inválido')


def validate_password_field(password, message):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(message)


def validate_role_field(role):
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')


def validate_color_field(color):
    if not is_valid_color(color):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
