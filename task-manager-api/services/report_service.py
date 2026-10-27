"""Relatórios: regras que cruzam tasks, users e categories."""
from datetime import timedelta

from config.constants import (
    HIGH_PRIORITY_THRESHOLD,
    PRIORITY_LABELS,
    RECENT_DAYS,
    VALID_STATUSES,
)
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage, utc_now


def summary_report():
    now = utc_now()
    by_status = Task.count_by(Task.status)
    by_priority = Task.count_by(Task.priority)

    overdue_tasks = Task.list_overdue()
    overdue_list = [{
        'id': task.id,
        'title': task.title,
        'due_date': str(task.due_date),
        'days_overdue': (now - task.due_date).days,
    } for task in overdue_tasks]

    since = now - timedelta(days=RECENT_DAYS)

    # Uma query agrupada em vez de uma consulta por usuário (N+1).
    task_totals = Task.count_by(Task.user_id)
    done_rows = db.session.execute(
        db.select(Task.user_id, db.func.count()).where(Task.status == 'done').group_by(Task.user_id)
    ).all()
    done_totals = {user_id: total for user_id, total in done_rows}
    user_stats = []
    for user in User.list_all():
        total = task_totals.get(user.id, 0)
        completed = done_totals.get(user.id, 0)
        user_stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': sum(by_status.values()),
            'total_users': User.count(),
            'total_categories': Category.count(),
        },
        'tasks_by_status': {status: by_status.get(status, 0) for status in VALID_STATUSES},
        'tasks_by_priority': {
            label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()
        },
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(since),
            'tasks_completed_last_7_days': Task.count_completed_since(since),
        },
        'user_productivity': user_stats,
    }


def user_report(user):
    tasks = Task.list_by_user(user.id)
    total = len(tasks)
    by_status = {status: 0 for status in VALID_STATUSES}
    for task in tasks:
        if task.status in by_status:
            by_status[task.status] += 1

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            'done': by_status['done'],
            'pending': by_status['pending'],
            'in_progress': by_status['in_progress'],
            'cancelled': by_status['cancelled'],
            'overdue': sum(1 for task in tasks if task.is_overdue()),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
            'completion_rate': calculate_percentage(by_status['done'], total),
        },
    }
