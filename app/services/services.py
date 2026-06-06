import logging
from app.core.database import db
from app.core.config import Config
from app.core.security import PasswordHasher, make_token
from app.models.models import User, Recording

logger = logging.getLogger(__name__)


# ─── AI ───────────────────────────────────────────────────────────────────────
class AIService:
    def feedback(self, rec: dict) -> dict:
        if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY.startswith('sk-your'):
            return self._mock(rec)
        try:
            import openai
            client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
            prompt = f"""You are a professional speech coach. Analyze this speech.

Speech Data:
- Transcript: {rec.get('transcript','No transcript')}
- Words: {rec.get('word_count',0)}
- Filler words: {rec.get('filler_word_count',0)}
- Repeated words: {rec.get('repeated_word_count',0)}
- Speed: {rec.get('speaking_speed',0):.1f} WPM
- Duration: {rec.get('duration_seconds',0)}s

Provide:
1) Overall Score (X/10)
2) Strengths
3) Filler word analysis
4) Speed feedback (ideal 120-150 WPM)
5) 3 specific improvement tips

Keep it encouraging but honest."""
            res = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=700)
            text  = res.choices[0].message.content.strip()
            score = self._score(text)
            return {'feedback': text, 'score': score, 'model': 'gpt-3.5-turbo'}
        except Exception as e:
            logger.error(f'OpenAI error: {e}')
            return self._mock(rec)

    def _mock(self, rec: dict) -> dict:
        fillers = rec.get('filler_word_count', 0)
        speed   = float(rec.get('speaking_speed', 0))
        words   = rec.get('word_count', 0)

        score = 8
        if fillers > 10: score -= 3
        elif fillers > 5: score -= 2
        elif fillers > 2: score -= 1
        if speed > 0 and (speed < 100 or speed > 200): score -= 1
        score = max(3, min(10, score))

        speed_line = (
            '• Record a longer session to get accurate speed data.'
            if speed == 0 else
            f'• Speaking too slowly ({speed:.0f} WPM). Aim for 120–150 WPM.'
            if speed < 100 else
            f'• A bit fast ({speed:.0f} WPM). Try to slow down slightly.'
            if speed > 180 else
            f'• Great speed ({speed:.0f} WPM) — in the ideal 120–150 WPM range!')

        text = f"""📊 OVERALL SCORE: {score} / 10

✅ STRENGTHS
{'• Strong session — ' + str(words) + ' words spoken with solid structure.' if words > 60 else '• Good start — keep recording every day to build fluency.'}
• Audio recorded, transcribed and saved successfully.

⚠️ FILLER WORDS  ({fillers} detected)
{
'• Outstanding — zero filler words. Perfectly clean delivery.' if fillers == 0 else
'• Only ' + str(fillers) + ' filler words — excellent control!' if fillers <= 3 else
str(fillers) + ' filler words found. Replace each with a deliberate 2-second pause — silence signals confidence.'
}

⏱️ SPEAKING SPEED
{speed_line}

💡 3 TIPS TO IMPROVE
1. Record yourself every day for 2 minutes — consistency compounds.
2. Pause after key points so ideas land with your audience.
3. Vary sentence length: short punchy lines create impact, then a longer sentence builds momentum."""
        return {'feedback': text, 'score': score, 'model': 'mock'}

    def _score(self, text: str) -> int:
        import re
        m = re.search(r'(\d+)\s*/\s*10', text)
        return int(m.group(1)) if m else 7


# ─── AUTH ─────────────────────────────────────────────────────────────────────
class AuthService:
    def register(self, username, email, password):
        if User.query.filter_by(email=email.lower()).first():
            return {'ok': False, 'msg': 'Email already registered', 'code': 409}
        if User.query.filter_by(username=username).first():
            return {'ok': False, 'msg': 'Username already taken', 'code': 409}
        user = User(username=username.strip(),
                    email=email.lower().strip(),
                    password_hash=PasswordHasher.hash(password))
        user.save()
        return {'ok': True, 'user': user.to_dict(), 'token': make_token(user.id)}

    def login(self, email, password):
        user = User.query.filter_by(email=email.lower().strip()).first()
        if not user or not PasswordHasher.verify(password, user.password_hash):
            return {'ok': False, 'msg': 'Invalid email or password', 'code': 401}
        if not user.is_active:
            return {'ok': False, 'msg': 'Account deactivated', 'code': 403}
        return {'ok': True, 'user': user.to_dict(), 'token': make_token(user.id)}


# ─── RECORDINGS ───────────────────────────────────────────────────────────────
class RecordingService:
    _ai = AIService()

    def create(self, data: dict, user_id=None):
        rec = Recording(
            user_id             = user_id,
            title               = data.get('title', 'Untitled Session'),
            audio_path          = data.get('audio_path', ''),
            transcript          = data.get('transcript', ''),
            word_count          = data.get('word_count', 0),
            filler_word_count   = data.get('filler_word_count', 0),
            repeated_word_count = data.get('repeated_word_count', 0),
            speaking_speed      = float(data.get('speaking_speed', 0)),
            frequent_words      = data.get('frequent_words'),
            duration_seconds    = data.get('duration_seconds', 0),
        )
        rec.save()
        # Update user stats
        if user_id:
            user = User.query.get(user_id)
            if user:
                n = user.total_sessions + 1
                user.avg_speed   = round(
                    (user.avg_speed * user.total_sessions + rec.speaking_speed) / n, 1)
                user.avg_fillers = round(
                    (user.avg_fillers * user.total_sessions + rec.filler_word_count) / n, 1)
                user.total_sessions = n
                db.session.commit()
        return rec

    def get_all(self, user_id=None):
        q = Recording.query
        if user_id: q = q.filter_by(user_id=user_id)
        return q.order_by(Recording.date_created.desc()).all()

    def get_one(self, rid):
        return Recording.query.get(rid)

    def delete(self, rid, user_id=None):
        rec = Recording.query.get(rid)
        if not rec: return False
        if user_id and rec.user_id and rec.user_id != user_id: return False
        rec.delete(); return True

    def get_feedback(self, rid):
        rec = Recording.query.get(rid)
        if not rec: return None
        result = self._ai.feedback(rec.to_dict())
        rec.ai_feedback = result['feedback']
        rec.ai_score    = result['score']
        db.session.commit()
        return result

    def get_stats(self, user_id):
        from sqlalchemy import func
        row = db.session.query(
            func.count(Recording.id),
            func.avg(Recording.speaking_speed),
            func.avg(Recording.filler_word_count),
            func.avg(Recording.word_count),
            func.avg(Recording.ai_score),
        ).filter_by(user_id=user_id).first()
        return {
            'total':       row[0] or 0,
            'avg_speed':   round(float(row[1] or 0), 1),
            'avg_fillers': round(float(row[2] or 0), 1),
            'avg_words':   round(float(row[3] or 0), 0),
            'avg_score':   round(float(row[4] or 0), 1) if row[4] else None,
        }


# ─── PROFILE ──────────────────────────────────────────────────────────────────
class ProfileService:
    def get(self, user_id):
        return User.query.get(user_id)

    def update(self, user_id, data: dict):
        user = User.query.get(user_id)
        if not user: return None
        if 'full_name' in data: user.full_name = data['full_name'].strip()
        if 'goal'      in data: user.goal      = data['goal'].strip()
        if 'password'  in data and len(data['password']) >= 6:
            user.password_hash = PasswordHasher.hash(data['password'])
        db.session.commit()
        return user
