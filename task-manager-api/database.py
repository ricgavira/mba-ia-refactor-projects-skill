from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def commit():
    """Commit com rollback automático; o erro segue para o error handler central."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
