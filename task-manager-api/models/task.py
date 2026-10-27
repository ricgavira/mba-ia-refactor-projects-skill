from sqlalchemy.orm import joinedload

from config.constants import DEFAULT_PRIORITY, DEFAULT_STATUS, FINISHED_STATUSES
from database import db
from utils.helpers import utc_now


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    # ---- regras de domínio -------------------------------------------------

    def is_overdue(self):
        return bool(
            self.due_date
            and self.due_date < utc_now()
            and self.status not in FINISHED_STATUSES
        )

    # ---- serialização ------------------------------------------------------

    def to_dict(self, include_overdue=False, include_relations=False):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }
        if include_overdue:
            data['overdue'] = self.is_overdue()
        if include_relations:
            data['user_name'] = self.user.name if self.user else None
            data['category_name'] = self.category.name if self.category else None
        return data

    def to_summary_dict(self):
        """Versão resumida usada em GET /users/<id>/tasks."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }

    # ---- consultas ---------------------------------------------------------

    @classmethod
    def list_all(cls, with_relations=False):
        stmt = db.select(cls)
        if with_relations:
            stmt = stmt.options(joinedload(cls.user), joinedload(cls.category))
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def list_by_user(cls, user_id):
        return db.session.execute(db.select(cls).where(cls.user_id == user_id)).scalars().all()

    @classmethod
    def search(cls, query=None, status=None, priority=None, user_id=None):
        stmt = db.select(cls)
        if query:
            stmt = stmt.where(db.or_(cls.title.like(f'%{query}%'), cls.description.like(f'%{query}%')))
        if status:
            stmt = stmt.where(cls.status == status)
        if priority is not None:
            stmt = stmt.where(cls.priority == priority)
        if user_id is not None:
            stmt = stmt.where(cls.user_id == user_id)
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def count_by(cls, column):
        """Contagem agrupada por coluna (status, priority, user_id...) em uma única query."""
        rows = db.session.execute(db.select(column, db.func.count()).group_by(column)).all()
        return {key: total for key, total in rows}

    @classmethod
    def overdue_filter(cls):
        return db.and_(cls.due_date.is_not(None), cls.due_date < utc_now(),
                       cls.status.not_in(FINISHED_STATUSES))

    @classmethod
    def list_overdue(cls):
        return db.session.execute(db.select(cls).where(cls.overdue_filter())).scalars().all()

    @classmethod
    def count_overdue(cls):
        return db.session.scalar(db.select(db.func.count()).select_from(cls).where(cls.overdue_filter()))

    @classmethod
    def count_created_since(cls, moment):
        return db.session.scalar(db.select(db.func.count()).select_from(cls).where(cls.created_at >= moment))

    @classmethod
    def count_completed_since(cls, moment):
        return db.session.scalar(
            db.select(db.func.count()).select_from(cls)
            .where(cls.status == 'done', cls.updated_at >= moment))
