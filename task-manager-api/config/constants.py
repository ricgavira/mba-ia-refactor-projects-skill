import re

VALID_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
DEFAULT_STATUS = 'pending'
FINISHED_STATUSES = ('done', 'cancelled')

VALID_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PASSWORD_LENGTH = 4

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2  # prioridade <= 2 conta como alta nos relatórios
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

DEFAULT_COLOR = '#000000'
DATE_FORMAT = '%Y-%m-%d'
RECENT_DAYS = 7

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
