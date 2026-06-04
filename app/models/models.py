# app/models/models.py
# Pattern: Active Record (via SQLAlchemy) + OOP inheritance from BaseModel

from app.core.database import db, BaseModel
from datetime import datetime


class User(BaseModel):
    """User model — central entity."""
    __tablename__ = 'users'

    full_name          = db.Column(db.String(100),  nullable=False)
    email              = db.Column(db.String(150),  nullable=False, unique=True, index=True)
    password_hash      = db.Column(db.String(255),  nullable=False)
    apex_level         = db.Column(db.SmallInteger, nullable=False, default=1)
    total_sessions     = db.Column(db.Integer,      nullable=False, default=0)
    avg_confidence     = db.Column(db.Float,        nullable=False, default=0.0)
    streak_days        = db.Column(db.SmallInteger, nullable=False, default=0)
    last_session_date  = db.Column(db.Date,         nullable=True)
    is_active          = db.Column(db.Boolean,      nullable=False, default=True)

    # Relationships
    scripts        = db.relationship('Script',       backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    sessions       = db.relationship('Session',      backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    refresh_tokens = db.relationship('RefreshToken', backref='owner', lazy='dynamic', cascade='all, delete-orphan')

    LEVEL_NAMES = [
        'Novice', 'Apprentice', 'Communicator', 'Presenter',
        'Speaker', 'Orator', 'Influencer', 'Authority',
        'Apex Elite', 'Grand Master',
    ]

    @property
    def level_name(self):
        idx = max(0, min(self.apex_level - 1, len(self.LEVEL_NAMES) - 1))
        return self.LEVEL_NAMES[idx]

    def to_dict(self):
        return {
            'id':             self.id,
            'full_name':      self.full_name,
            'email':          self.email,
            'apex_level':     self.apex_level,
            'level_name':     self.level_name,
            'total_sessions': self.total_sessions,
            'avg_confidence': round(self.avg_confidence, 1),
            'streak_days':    self.streak_days,
            'created_at':     self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<User {self.email}>'


class Script(BaseModel):
    """Script model — a user's speech text."""
    __tablename__ = 'scripts'

    user_id              = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=False, index=True)
    title                = db.Column(db.String(200), nullable=False)
    raw_text             = db.Column(db.Text,        nullable=False)
    apexified_text       = db.Column(db.Text,        nullable=True)
    audience_type        = db.Column(db.String(100), nullable=False, default='General')
    estimated_duration   = db.Column(db.Integer,     nullable=False, default=0)
    is_apexified         = db.Column(db.Boolean,     nullable=False, default=False)

    # Relationships
    qa_list  = db.relationship('QASimulation', backref='script', lazy='dynamic', cascade='all, delete-orphan')
    sessions = db.relationship('Session',      backref='script', lazy='dynamic', foreign_keys='Session.script_id')

    @property
    def duration_label(self):
        mins = self.estimated_duration // 60
        secs = self.estimated_duration % 60
        return f"{mins}m {secs}s" if mins else f"{secs}s"

    def to_dict(self):
        return {
            'id':                  self.id,
            'user_id':             self.user_id,
            'title':               self.title,
            'raw_text':            self.raw_text,
            'apexified_text':      self.apexified_text,
            'audience_type':       self.audience_type,
            'estimated_duration':  self.estimated_duration,
            'duration_label':      self.duration_label,
            'is_apexified':        self.is_apexified,
            'created_at':          self.created_at.isoformat() if self.created_at else None,
            'updated_at':          self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<Script {self.title}>'


class QASimulation(BaseModel):
    """AI-generated Q&A pairs for a script."""
    __tablename__ = 'qa_simulations'

    script_id        = db.Column(db.Integer, db.ForeignKey('scripts.id'), nullable=False, index=True)
    question         = db.Column(db.Text,        nullable=False)
    suggested_answer = db.Column(db.Text,        nullable=False)
    difficulty       = db.Column(db.Enum('easy', 'medium', 'hard'), nullable=False, default='medium')

    def to_dict(self):
        return {
            'id':               self.id,
            'script_id':        self.script_id,
            'question':         self.question,
            'suggested_answer': self.suggested_answer,
            'difficulty':       self.difficulty,
        }


class Session(BaseModel):
    """A single practice session."""
    __tablename__ = 'sessions'

    user_id            = db.Column(db.Integer, db.ForeignKey('users.id'),   nullable=False, index=True)
    script_id          = db.Column(db.Integer, db.ForeignKey('scripts.id'), nullable=True)
    duration_seconds   = db.Column(db.Integer, nullable=False, default=0)
    confidence_score   = db.Column(db.Float,   nullable=False, default=0.0)
    enthusiasm_score   = db.Column(db.Float,   nullable=False, default=0.0)
    authority_score    = db.Column(db.Float,   nullable=False, default=0.0)
    overall_score      = db.Column(db.Float,   nullable=False, default=0.0)
    grade              = db.Column(db.Enum('S+','A','B','C','D'), nullable=False, default='D')
    filler_word_count  = db.Column(db.Integer, nullable=False, default=0)
    posture_alerts     = db.Column(db.Integer, nullable=False, default=0)
    transcription      = db.Column(db.Text,    nullable=True)
    audio_path         = db.Column(db.String(255), nullable=True)
    status             = db.Column(db.Enum('active','completed','abandoned'), nullable=False, default='active')
    completed_at       = db.Column(db.DateTime, nullable=True)

    # Relationships
    filler_events  = db.relationship('FillerWordEvent', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    posture_events = db.relationship('PostureEvent',    backref='session', lazy='dynamic', cascade='all, delete-orphan')
    coaching_tips  = db.relationship('AICoachingTip',   backref='session', lazy='dynamic', cascade='all, delete-orphan')

    @classmethod
    def compute_grade(cls, score: float) -> str:
        if score >= 90: return 'S+'
        if score >= 80: return 'A'
        if score >= 70: return 'B'
        if score >= 60: return 'C'
        return 'D'

    @classmethod
    def compute_overall(cls, confidence, enthusiasm, authority) -> float:
        return round(confidence * 0.4 + enthusiasm * 0.3 + authority * 0.3, 2)

    @property
    def duration_label(self):
        m = self.duration_seconds // 60
        s = self.duration_seconds % 60
        return f"{str(m).zfill(2)}:{str(s).zfill(2)}"

    def to_dict(self):
        return {
            'id':               self.id,
            'user_id':          self.user_id,
            'script_id':        self.script_id,
            'duration_seconds': self.duration_seconds,
            'duration_label':   self.duration_label,
            'confidence_score': self.confidence_score,
            'enthusiasm_score': self.enthusiasm_score,
            'authority_score':  self.authority_score,
            'overall_score':    self.overall_score,
            'grade':            self.grade,
            'filler_word_count':self.filler_word_count,
            'posture_alerts':   self.posture_alerts,
            'transcription':    self.transcription,
            'status':           self.status,
            'created_at':       self.created_at.isoformat() if self.created_at else None,
            'completed_at':     self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f'<Session {self.id} grade={self.grade}>'


class FillerWordEvent(BaseModel):
    """Individual filler word detection event during a session."""
    __tablename__ = 'filler_word_events'

    session_id        = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    word              = db.Column(db.String(50), nullable=False)
    timestamp_seconds = db.Column(db.Float,      nullable=False)

    def to_dict(self):
        return {
            'id':               self.id,
            'session_id':       self.session_id,
            'word':             self.word,
            'timestamp_seconds':self.timestamp_seconds,
        }


class PostureEvent(BaseModel):
    """Posture detection event during a session."""
    __tablename__ = 'posture_events'

    session_id        = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    event_type        = db.Column(db.Enum('slouch','crossed_arms','confident_gesture','eye_contact'), nullable=False)
    timestamp_seconds = db.Column(db.Float,  nullable=False)
    duration_seconds  = db.Column(db.Float,  nullable=False, default=0.0)

    def to_dict(self):
        return {
            'id':               self.id,
            'session_id':       self.session_id,
            'event_type':       self.event_type,
            'timestamp_seconds':self.timestamp_seconds,
            'duration_seconds': self.duration_seconds,
        }


class AICoachingTip(BaseModel):
    """AI-generated coaching tip for a completed session."""
    __tablename__ = 'ai_coaching_tips'

    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    tip_type   = db.Column(db.Enum('strength','improvement'), nullable=False)
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text,        nullable=False)
    icon_emoji = db.Column(db.String(10),  nullable=False, default='💡')

    def to_dict(self):
        return {
            'id':        self.id,
            'tip_type':  self.tip_type,
            'title':     self.title,
            'body':      self.body,
            'icon_emoji':self.icon_emoji,
        }


class RefreshToken(db.Model):
    """
    JWT refresh token store.
    Does NOT extend BaseModel — the refresh_tokens table has no updated_at column.
    """
    __tablename__ = 'refresh_tokens'

    id         = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer,     db.ForeignKey('users.id'), nullable=False, index=True)
    token_hash = db.Column(db.String(255), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime,    nullable=False)
    revoked    = db.Column(db.Boolean,     nullable=False, default=False)
    created_at = db.Column(db.DateTime,    server_default=db.func.now(), nullable=False)

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        return not self.revoked and not self.is_expired