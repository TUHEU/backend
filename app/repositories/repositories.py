# app/repositories/repositories.py
# Pattern: Repository Pattern — abstracts all DB queries behind clean interfaces
#          Abstract base class enforces the contract; concrete classes implement it.

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime, timedelta
import hashlib

from app.core.database import db
from app.models.models import (
    User, Script, QASimulation, Session,
    FillerWordEvent, PostureEvent, AICoachingTip, RefreshToken
)


# =============================================================================
# ABSTRACT REPOSITORY BASE
# =============================================================================
class AbstractRepository(ABC):
    """
    Generic repository interface.
    Forces all concrete repositories to implement CRUD operations.
    """
    @abstractmethod
    def find_by_id(self, record_id: int):
        pass

    @abstractmethod
    def find_all(self) -> list:
        pass

    @abstractmethod
    def save(self, entity) -> object:
        pass

    @abstractmethod
    def delete(self, entity) -> None:
        pass


# =============================================================================
# USER REPOSITORY
# =============================================================================
class UserRepository(AbstractRepository):

    def find_by_id(self, record_id: int) -> Optional[User]:
        return User.query.get(record_id)

    def find_all(self) -> List[User]:
        return User.query.filter_by(is_active=True).all()

    def find_by_email(self, email: str) -> Optional[User]:
        return User.query.filter_by(email=email.lower().strip()).first()

    def save(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

    def delete(self, user: User) -> None:
        user.is_active = False
        db.session.commit()

    def update_stats_after_session(self, user: User, new_confidence: float) -> User:
        """Recalculate running average and level after a session completes."""
        total = user.total_sessions + 1
        user.avg_confidence = round(
            (user.avg_confidence * user.total_sessions + new_confidence) / total, 2
        )
        user.total_sessions = total
        user.last_session_date = datetime.utcnow().date()

        # Streak logic
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()
        if user.last_session_date == yesterday:
            user.streak_days += 1
        else:
            user.streak_days = 1

        # Level-up: every 4 sessions, level increases (max 10)
        if total % 4 == 0:
            user.apex_level = min(user.apex_level + 1, 10)

        db.session.commit()
        return user


# =============================================================================
# SCRIPT REPOSITORY
# =============================================================================
class ScriptRepository(AbstractRepository):

    def find_by_id(self, record_id: int) -> Optional[Script]:
        return Script.query.get(record_id)

    def find_all(self) -> List[Script]:
        return Script.query.all()

    def find_by_user(self, user_id: int) -> List[Script]:
        return (Script.query
                .filter_by(user_id=user_id)
                .order_by(Script.created_at.desc())
                .all())

    def find_by_user_and_id(self, user_id: int, script_id: int) -> Optional[Script]:
        return Script.query.filter_by(id=script_id, user_id=user_id).first()

    def save(self, script: Script) -> Script:
        db.session.add(script)
        db.session.commit()
        return script

    def delete(self, script: Script) -> None:
        db.session.delete(script)
        db.session.commit()

    def save_qa_list(self, script_id: int, qa_data: list) -> List[QASimulation]:
        # Delete old Q&A for this script
        QASimulation.query.filter_by(script_id=script_id).delete()
        items = []
        for item in qa_data:
            qa = QASimulation(
                script_id        = script_id,
                question         = item['question'],
                suggested_answer = item['suggested_answer'],
                difficulty       = item.get('difficulty', 'medium'),
            )
            db.session.add(qa)
            items.append(qa)
        db.session.commit()
        return items

    def get_qa_list(self, script_id: int) -> List[QASimulation]:
        return QASimulation.query.filter_by(script_id=script_id).all()


# =============================================================================
# SESSION REPOSITORY
# =============================================================================
class SessionRepository(AbstractRepository):

    def find_by_id(self, record_id: int) -> Optional[Session]:
        return Session.query.get(record_id)

    def find_all(self) -> List[Session]:
        return Session.query.all()

    def find_by_user(self, user_id: int, limit: int = 20) -> List[Session]:
        return (Session.query
                .filter_by(user_id=user_id)
                .order_by(Session.created_at.desc())
                .limit(limit)
                .all())

    def find_active_by_user(self, user_id: int) -> Optional[Session]:
        return Session.query.filter_by(user_id=user_id, status='active').first()

    def save(self, session: Session) -> Session:
        db.session.add(session)
        db.session.commit()
        return session

    def delete(self, session: Session) -> None:
        db.session.delete(session)
        db.session.commit()

    def add_filler_event(self, session_id: int, word: str, timestamp: float) -> FillerWordEvent:
        event = FillerWordEvent(
            session_id=session_id,
            word=word,
            timestamp_seconds=timestamp,
        )
        db.session.add(event)
        # Increment counter
        Session.query.filter_by(id=session_id).update(
            {'filler_word_count': Session.filler_word_count + 1}
        )
        db.session.commit()
        return event

    def add_posture_event(self, session_id: int, event_type: str,
                          timestamp: float, duration: float = 0.0) -> PostureEvent:
        event = PostureEvent(
            session_id=session_id,
            event_type=event_type,
            timestamp_seconds=timestamp,
            duration_seconds=duration,
        )
        db.session.add(event)
        if event_type in ('slouch', 'crossed_arms'):
            Session.query.filter_by(id=session_id).update(
                {'posture_alerts': Session.posture_alerts + 1}
            )
        db.session.commit()
        return event

    def save_coaching_tips(self, session_id: int, tips: list) -> List[AICoachingTip]:
        AICoachingTip.query.filter_by(session_id=session_id).delete()
        result = []
        for t in tips:
            tip = AICoachingTip(
                session_id = session_id,
                tip_type   = t['tip_type'],
                title      = t['title'],
                body       = t['body'],
                icon_emoji = t.get('icon_emoji', '💡'),
            )
            db.session.add(tip)
            result.append(tip)
        db.session.commit()
        return result

    def get_full_report(self, session_id: int) -> dict:
        session = self.find_by_id(session_id)
        if not session:
            return {}
        return {
            'session':       session.to_dict(),
            'filler_events': [e.to_dict() for e in session.filler_events],
            'posture_events':[e.to_dict() for e in session.posture_events],
            'coaching_tips': [t.to_dict() for t in session.coaching_tips],
        }


# =============================================================================
# TOKEN REPOSITORY
# =============================================================================
class TokenRepository(AbstractRepository):

    def find_by_id(self, record_id: int) -> Optional[RefreshToken]:
        return RefreshToken.query.get(record_id)

    def find_all(self) -> List[RefreshToken]:
        return RefreshToken.query.all()

    def find_valid_token(self, raw_token: str) -> Optional[RefreshToken]:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        token = RefreshToken.query.filter_by(token_hash=token_hash, revoked=False).first()
        return token if token and token.is_valid else None

    def save(self, token: RefreshToken) -> RefreshToken:
        db.session.add(token)
        db.session.commit()
        return token

    def delete(self, token: RefreshToken) -> None:
        db.session.delete(token)
        db.session.commit()

    def revoke_all_for_user(self, user_id: int) -> None:
        RefreshToken.query.filter_by(user_id=user_id).update({'revoked': True})
        db.session.commit()

    def create(self, user_id: int, raw_token: str, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(
            user_id    = user_id,
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at = expires_at,
        )
        return self.save(token)
