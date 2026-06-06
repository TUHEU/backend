from app.core.database import db, BaseModel

class User(BaseModel):
    __tablename__  = 'users'
    username       = db.Column(db.String(100), nullable=False, unique=True)
    email          = db.Column(db.String(150), nullable=False,
                               unique=True, index=True)
    password_hash  = db.Column(db.String(255), nullable=False)
    full_name      = db.Column(db.String(150))
    goal           = db.Column(db.Text)
    total_sessions = db.Column(db.Integer, default=0)
    avg_speed      = db.Column(db.Float,   default=0.0)
    avg_fillers    = db.Column(db.Float,   default=0.0)
    is_active      = db.Column(db.Boolean, default=True)

    recordings = db.relationship('Recording', backref='user',
                                 lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {'id': self.id, 'username': self.username, 'email': self.email,
                'full_name': self.full_name, 'goal': self.goal,
                'total_sessions': self.total_sessions,
                'avg_speed': round(self.avg_speed, 1),
                'avg_fillers': round(self.avg_fillers, 1)}


class Recording(BaseModel):
    __tablename__       = 'recordings'
    user_id             = db.Column(db.Integer,
                              db.ForeignKey('users.id'), index=True)
    title               = db.Column(db.String(200), nullable=False)
    audio_path          = db.Column(db.String(500), nullable=False)
    transcript          = db.Column(db.Text)
    word_count          = db.Column(db.Integer, default=0)
    filler_word_count   = db.Column(db.Integer, default=0)
    repeated_word_count = db.Column(db.Integer, default=0)
    speaking_speed      = db.Column(db.Float,   default=0.0)
    frequent_words      = db.Column(db.Text)
    ai_feedback         = db.Column(db.Text)
    ai_score            = db.Column(db.SmallInteger)
    duration_seconds    = db.Column(db.Integer, default=0)
    date_created        = db.Column(db.DateTime,
                              server_default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id, 'user_id': self.user_id, 'title': self.title,
            'audio_path': self.audio_path, 'transcript': self.transcript,
            'word_count': self.word_count,
            'filler_word_count': self.filler_word_count,
            'repeated_word_count': self.repeated_word_count,
            'speaking_speed': round(self.speaking_speed, 1),
            'frequent_words': self.frequent_words,
            'ai_feedback': self.ai_feedback, 'ai_score': self.ai_score,
            'duration_seconds': self.duration_seconds,
            'date_created': self.date_created.isoformat()
                if self.date_created else None,
        }
