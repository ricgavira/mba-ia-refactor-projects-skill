from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import DEFAULT_ROLE
from database import db
from utils.helpers import utc_now


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        # Allowlist: o hash da senha nunca sai do model.
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password, pwd)

    @classmethod
    def list_all(cls):
        return db.session.execute(db.select(cls)).scalars().all()

    @classmethod
    def find_by_email(cls, email):
        return db.session.execute(db.select(cls).where(cls.email == email)).scalars().first()

    @classmethod
    def count(cls):
        return db.session.scalar(db.select(db.func.count()).select_from(cls))
