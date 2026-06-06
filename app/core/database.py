from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db      = SQLAlchemy()
migrate = Migrate()

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # No shared created_at — Recording uses date_created,
    # User's created_at is a DB-only column (DEFAULT CURRENT_TIMESTAMP).

    def save(self):
        db.session.add(self); db.session.commit(); return self

    def delete(self):
        db.session.delete(self); db.session.commit()

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
