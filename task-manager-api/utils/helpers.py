from datetime import datetime, timezone

from config.constants import DATE_FORMAT, EMAIL_PATTERN


def utc_now():
    """UTC atual sem tzinfo: substitui datetime.utcnow() (deprecated) mantendo
    a compatibilidade com os datetimes naive gravados no banco."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_date(date_string):
    """Converte 'YYYY-MM-DD' em datetime; devolve None se o formato for inválido."""
    try:
        return datetime.strptime(date_string, DATE_FORMAT)
    except (TypeError, ValueError):
        return None


def validate_email(email):
    return isinstance(email, str) and bool(EMAIL_PATTERN.match(email))


def is_valid_color(color):
    return isinstance(color, str) and len(color) == 7 and color.startswith('#')


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)
