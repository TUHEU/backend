# app/core/database.py
# Pattern: Singleton — single db instance shared across the app

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db      = SQLAlchemy()
migrate = Migrate()


class BaseModel(db.Model):
    """
    Abstract base model — OOP inheritance pattern.
    All models extend this to get id + timestamps for free.
    """
    __abstract__ = True

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False
    )

    def to_dict(self):
        """Serialize model to dict — override in subclasses for custom output."""
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
        }

    def save(self):
        """Persist self to DB."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Delete self from DB."""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, record_id):
        return cls.query.get(record_id)

    @classmethod
    def get_all(cls):
        return cls.query.all()
