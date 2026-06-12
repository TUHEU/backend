# backend/models/user_model.py
import bcrypt
from datetime import datetime
from config.database import db_cursor


class User:
    """OOP representation of a users row."""

    def __init__(self, id=None, full_name='', email='', phone=None,
                 password_hash=None, date_of_birth=None, profile_image_url=None,
                 is_email_verified=False, bio=None, job_title=None,
                 company=None, created_at=None, updated_at=None):
        self.id                = id
        self.full_name         = full_name
        self.email             = email
        self.phone             = phone
        self.password_hash     = password_hash
        self.date_of_birth     = date_of_birth
        self.profile_image_url = profile_image_url
        self.is_email_verified = bool(is_email_verified)
        self.bio               = bio
        self.job_title         = job_title
        self.company           = company
        self.created_at        = created_at
        self.updated_at        = updated_at

    # ── Class methods (factory / queries) ─────────────────────────────────────

    @classmethod
    def from_row(cls, row: dict) -> 'User':
        return cls(**{k: v for k, v in row.items() if k in cls.__init__.__code__.co_varnames})

    @classmethod
    def find_by_email(cls, email: str) -> 'User | None':
        with db_cursor() as (_, cursor):
            cursor.execute('SELECT * FROM users WHERE email = %s LIMIT 1', (email,))
            row = cursor.fetchone()
        return cls.from_row(row) if row else None

    @classmethod
    def find_by_id(cls, user_id: int) -> 'User | None':
        with db_cursor() as (_, cursor):
            cursor.execute('SELECT * FROM users WHERE id = %s LIMIT 1', (user_id,))
            row = cursor.fetchone()
        return cls.from_row(row) if row else None

    @classmethod
    def create(cls, full_name: str, email: str, password: str,
               phone: str = None, date_of_birth: str = None,
               profile_image_url: str = None) -> 'User':
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(
                """INSERT INTO users
                     (full_name, email, phone, password_hash, date_of_birth, profile_image_url)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (full_name, email, phone, password_hash, date_of_birth, profile_image_url),
            )
            user_id = cursor.lastrowid
        return cls.find_by_id(user_id)

    # ── Instance methods ───────────────────────────────────────────────────────

    def check_password(self, plain: str) -> bool:
        if not self.password_hash:
            return False
        return bcrypt.checkpw(plain.encode(), self.password_hash.encode())

    def set_password(self, new_password: str) -> None:
        new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(
                'UPDATE users SET password_hash = %s WHERE id = %s',
                (new_hash, self.id),
            )
        self.password_hash = new_hash

    def verify_email(self) -> None:
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(
                'UPDATE users SET is_email_verified = 1 WHERE id = %s', (self.id,)
            )
        self.is_email_verified = True

    def update_profile(self, **fields) -> None:
        allowed = {'full_name', 'phone', 'date_of_birth', 'bio', 'job_title',
                   'company', 'profile_image_url'}
        updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
        if not updates:
            return
        set_clause = ', '.join(f'{k} = %s' for k in updates)
        values = list(updates.values()) + [self.id]
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(f'UPDATE users SET {set_clause} WHERE id = %s', values)
        for k, v in updates.items():
            setattr(self, k, v)

    def to_dict(self) -> dict:
        dob = self.date_of_birth
        if isinstance(dob, datetime):
            dob = dob.date().isoformat()
        elif dob is not None:
            dob = str(dob)
        return {
            'id':                self.id,
            'full_name':         self.full_name,
            'email':             self.email,
            'phone':             self.phone,
            'date_of_birth':     dob,
            'profile_image_url': self.profile_image_url,
            'is_email_verified': self.is_email_verified,
            'bio':               self.bio,
            'job_title':         self.job_title,
            'company':           self.company,
            'created_at':        str(self.created_at) if self.created_at else None,
        }

    def __repr__(self):
        return f'<User id={self.id} email={self.email}>'
