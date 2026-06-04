# app/services/services.py
# Pattern: Service Layer — all business logic lives here, not in routes
#          Strategy Pattern for AI providers (OpenAI / Hume)

import os
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional

import openai
import requests

from app.core.config import get_config
from app.core.security import PasswordHasher, TokenManager
from app.models.models import User, Script, Session
from app.repositories.repositories import (
    UserRepository, ScriptRepository, SessionRepository, TokenRepository
)

logger = logging.getLogger(__name__)
cfg    = get_config()


# =============================================================================
# STRATEGY PATTERN — AI Providers
# =============================================================================
class AIProvider(ABC):
    """Abstract AI provider — Strategy interface."""
    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> dict:
        pass

    @abstractmethod
    def analyze_emotion(self, audio_bytes: bytes) -> dict:
        pass


class OpenAIProvider(AIProvider):
    """Concrete strategy: OpenAI Whisper + GPT-4o."""

    def __init__(self):
        openai.api_key = cfg.OPENAI_API_KEY
        self.client    = openai.OpenAI(api_key=cfg.OPENAI_API_KEY)

    def transcribe(self, audio_bytes: bytes) -> dict:
        """Call Whisper API, return transcript + filler words."""
        try:
            import tempfile, os
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            with open(tmp_path, 'rb') as f:
                response = self.client.audio.transcriptions.create(
                    model='whisper-1',
                    file=f,
                    response_format='verbose_json',
                    timestamp_granularities=['word'],
                )
            os.unlink(tmp_path)

            text  = response.text
            words = getattr(response, 'words', [])

            filler_words = ['um','uh','like','you know','sort of',
                            'kind of','basically','literally','actually']
            detected = [
                {'word': w.word, 'timestamp': w.start}
                for w in words if w.word.lower().strip() in filler_words
            ]
            return {'transcription': text, 'filler_events': detected, 'success': True}
        except Exception as e:
            logger.error(f"Whisper error: {e}")
            return {'transcription': '', 'filler_events': [], 'success': False, 'error': str(e)}

    def analyze_emotion(self, audio_bytes: bytes) -> dict:
        """Stub — Hume AI handles emotion; OpenAI doesn't."""
        return {}

    def apexify_script(self, raw_text: str) -> str:
        """Refine raw speech text with GPT-4o."""
        try:
            response = self.client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {'role': 'system', 'content': cfg.GPT_APEXIFY_SYSTEM_PROMPT},
                    {'role': 'user',   'content': raw_text},
                ],
                max_tokens=1500,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"GPT-4o apexify error: {e}")
            raise

    def generate_qa(self, script_text: str) -> list:
        """Generate 5 Q&A pairs for a script."""
        try:
            response = self.client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {'role': 'system', 'content': cfg.GPT_QA_SYSTEM_PROMPT},
                    {'role': 'user',   'content': script_text},
                ],
                max_tokens=1200,
                temperature=0.8,
            )
            raw = response.choices[0].message.content.strip()
            raw = raw.replace('```json', '').replace('```', '').strip()
            return json.loads(raw)
        except Exception as e:
            logger.error(f"GPT-4o Q&A error: {e}")
            raise

    def generate_coaching_tips(self, session_data: dict) -> list:
        prompt = (
            f"Based on this speech session:\n"
            f"- Confidence: {session_data.get('confidence_score')}%\n"
            f"- Enthusiasm: {session_data.get('enthusiasm_score')}%\n"
            f"- Authority: {session_data.get('authority_score')}%\n"
            f"- Filler words: {session_data.get('filler_word_count')}\n"
            f"- Posture alerts: {session_data.get('posture_alerts')}\n\n"
            f"Generate 4 coaching tips (2 strengths, 2 improvements). "
            f"Return ONLY valid JSON array: "
            f'[{{"tip_type":"strength|improvement","title":"...","body":"...","icon_emoji":"..."}}]'
        )
        try:
            response = self.client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {'role': 'system', 'content': 'You are an expert public speaking coach.'},
                    {'role': 'user',   'content': prompt},
                ],
                max_tokens=800,
                temperature=0.6,
            )
            raw = response.choices[0].message.content.strip()
            raw = raw.replace('```json', '').replace('```', '').strip()
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Coaching tips error: {e}")
            return []


class HumeAIProvider:
    """Hume AI prosody analysis — Confidence, Enthusiasm, Authority."""

    BASE_URL = 'https://api.hume.ai/v0/batch/jobs'

    def __init__(self):
        self.api_key = cfg.HUME_API_KEY

    def analyze_prosody(self, audio_bytes: bytes) -> dict:
        """Submit audio to Hume AI, poll for results."""
        if not self.api_key:
            return self._mock_scores()
        try:
            headers = {'X-Hume-Api-Key': self.api_key}
            files   = {'file': ('audio.wav', audio_bytes, 'audio/wav')}
            data    = {'json': json.dumps({'models': {'prosody': {}}})}

            response = requests.post(
                self.BASE_URL, headers=headers, files=files, data=data, timeout=30
            )
            response.raise_for_status()
            job_id = response.json().get('job_id')

            for _ in range(10):
                time.sleep(2)
                result = requests.get(
                    f"{self.BASE_URL}/{job_id}/predictions",
                    headers=headers, timeout=10
                )
                if result.status_code == 200:
                    return self._parse_prosody(result.json())
            return self._mock_scores()
        except Exception as e:
            logger.error(f"Hume AI error: {e}")
            return self._mock_scores()

    def _parse_prosody(self, data: dict) -> dict:
        try:
            predictions = data[0]['results']['predictions'][0]['models']['prosody']['grouped_predictions']
            scores_map  = {}
            for group in predictions:
                for pred in group.get('predictions', []):
                    for emotion in pred.get('emotions', []):
                        name  = emotion['name'].lower()
                        score = emotion['score']
                        scores_map[name] = max(scores_map.get(name, 0), score)

            confidence  = scores_map.get('confidence',  0.5) * 100
            enthusiasm  = scores_map.get('excitement',  0.5) * 100
            authority   = scores_map.get('determination',0.5)* 100
            return {
                'confidence_score': round(confidence, 2),
                'enthusiasm_score': round(enthusiasm, 2),
                'authority_score':  round(authority,  2),
            }
        except Exception:
            return self._mock_scores()

    def _mock_scores(self) -> dict:
        """Fallback when API key is not set — for development."""
        import random
        return {
            'confidence_score': round(random.uniform(55, 90), 2),
            'enthusiasm_score': round(random.uniform(45, 85), 2),
            'authority_score':  round(random.uniform(60, 92), 2),
        }


# =============================================================================
# AUTH SERVICE
# =============================================================================
class AuthService:
    """Handles user registration, login, token management."""

    def __init__(self):
        self.user_repo  = UserRepository()
        self.token_repo = TokenRepository()

    def register(self, full_name: str, email: str, password: str) -> dict:
        if self.user_repo.find_by_email(email):
            return {'success': False, 'message': 'Email already registered', 'code': 409}

        user = User(
            full_name     = full_name.strip(),
            email         = email.lower().strip(),
            password_hash = PasswordHasher.hash(password),
        )
        self.user_repo.save(user)
        tokens = self._issue_tokens(user)
        return {'success': True, 'user': user.to_dict(), **tokens}

    def login(self, email: str, password: str) -> dict:
        user = self.user_repo.find_by_email(email)
        if not user or not PasswordHasher.verify(password, user.password_hash):
            return {'success': False, 'message': 'Invalid email or password', 'code': 401}
        if not user.is_active:
            return {'success': False, 'message': 'Account deactivated', 'code': 403}

        tokens = self._issue_tokens(user)
        return {'success': True, 'user': user.to_dict(), **tokens}

    def refresh(self, raw_refresh_token: str) -> dict:
        token = self.token_repo.find_valid_token(raw_refresh_token)
        if not token:
            return {'success': False, 'message': 'Invalid or expired refresh token', 'code': 401}

        user = self.user_repo.find_by_id(token.user_id)
        access_token = TokenManager.create_access(user.id)
        return {'success': True, 'access_token': access_token}

    def logout(self, user_id: int) -> dict:
        self.token_repo.revoke_all_for_user(user_id)
        return {'success': True, 'message': 'Logged out'}

    def _issue_tokens(self, user: User) -> dict:
        access_token              = TokenManager.create_access(user.id)
        raw_refresh, expires, _   = TokenManager.create_refresh()
        self.token_repo.create(user.id, raw_refresh, expires)
        return {'access_token': access_token, 'refresh_token': raw_refresh}


# =============================================================================
# SCRIPT SERVICE
# =============================================================================
class ScriptService:
    """Handles script CRUD + AI apexification + Q&A generation."""

    def __init__(self):
        self.repo     = ScriptRepository()
        self.ai       = OpenAIProvider()

    def get_all(self, user_id: int) -> list:
        return [s.to_dict() for s in self.repo.find_by_user(user_id)]

    def get_one(self, user_id: int, script_id: int) -> dict:
        script = self.repo.find_by_user_and_id(user_id, script_id)
        if not script:
            return {'success': False, 'message': 'Script not found', 'code': 404}
        data = script.to_dict()
        data['qa_list'] = [q.to_dict() for q in self.repo.get_qa_list(script_id)]
        return {'success': True, 'script': data}

    def create(self, user_id: int, payload: dict) -> dict:
        script = Script(
            user_id            = user_id,
            title              = payload.get('title', 'Untitled').strip(),
            raw_text           = payload.get('raw_text', '').strip(),
            audience_type      = payload.get('audience_type', 'General'),
            estimated_duration = payload.get('estimated_duration', 0),
        )
        self.repo.save(script)
        return {'success': True, 'script': script.to_dict()}

    def update(self, user_id: int, script_id: int, payload: dict) -> dict:
        script = self.repo.find_by_user_and_id(user_id, script_id)
        if not script:
            return {'success': False, 'message': 'Script not found', 'code': 404}

        for field in ('title', 'raw_text', 'audience_type', 'estimated_duration'):
            if field in payload:
                setattr(script, field, payload[field])

        self.repo.save(script)
        return {'success': True, 'script': script.to_dict()}

    def delete(self, user_id: int, script_id: int) -> dict:
        script = self.repo.find_by_user_and_id(user_id, script_id)
        if not script:
            return {'success': False, 'message': 'Script not found', 'code': 404}
        self.repo.delete(script)
        return {'success': True, 'message': 'Script deleted'}

    def apexify(self, user_id: int, script_id: int) -> dict:
        script = self.repo.find_by_user_and_id(user_id, script_id)
        if not script:
            return {'success': False, 'message': 'Script not found', 'code': 404}
        if not script.raw_text.strip():
            return {'success': False, 'message': 'Script has no text to apexify', 'code': 400}
        try:
            refined = self.ai.apexify_script(script.raw_text)
            script.apexified_text = refined
            script.is_apexified   = True
            self.repo.save(script)
            return {'success': True, 'script': script.to_dict()}
        except Exception as e:
            return {'success': False, 'message': f'AI error: {str(e)}', 'code': 503}

    def generate_qa(self, user_id: int, script_id: int) -> dict:
        script = self.repo.find_by_user_and_id(user_id, script_id)
        if not script:
            return {'success': False, 'message': 'Script not found', 'code': 404}
        try:
            text  = script.apexified_text or script.raw_text
            items = self.ai.generate_qa(text)
            saved = self.repo.save_qa_list(script_id, items)
            return {'success': True, 'qa_list': [q.to_dict() for q in saved]}
        except Exception as e:
            return {'success': False, 'message': f'AI error: {str(e)}', 'code': 503}


# =============================================================================
# SESSION SERVICE
# =============================================================================
class SessionService:
    """Handles live practice session lifecycle."""

    def __init__(self):
        self.repo      = SessionRepository()
        self.user_repo = UserRepository()
        self.whisper   = OpenAIProvider()
        self.hume      = HumeAIProvider()
        self.ai        = OpenAIProvider()

    def start(self, user_id: int, script_id: Optional[int] = None) -> dict:
        # Abandon any previously active session
        existing = self.repo.find_active_by_user(user_id)
        if existing:
            existing.status = 'abandoned'
            self.repo.save(existing)

        session = Session(user_id=user_id, script_id=script_id, status='active')
        self.repo.save(session)
        return {'success': True, 'session_id': session.id}

    def process_audio_chunk(self, session_id: int, audio_bytes: bytes) -> dict:
        """
        Called every ~5s during live practice.
        Runs Whisper + Hume in parallel (simple sequential here for clarity).
        """
        session = self.repo.find_by_id(session_id)
        if not session or session.status != 'active':
            return {'success': False, 'message': 'Session not active', 'code': 400}

        # 1. Transcription
        transcript_result = self.whisper.transcribe(audio_bytes)

        # 2. Emotion scores
        emotion_result = self.hume.analyze_prosody(audio_bytes)

        # 3. Save filler word events
        for fe in transcript_result.get('filler_events', []):
            self.repo.add_filler_event(session_id, fe['word'], fe['timestamp'])

        # 4. Accumulate transcription
        new_text = transcript_result.get('transcription', '')
        if new_text:
            session.transcription = ((session.transcription or '') + ' ' + new_text).strip()

        # 5. Update running scores (rolling average)
        n = session.filler_word_count or 1
        session.confidence_score = round(
            (session.confidence_score * (n - 1) + emotion_result.get('confidence_score', 0)) / n, 2
        )
        session.enthusiasm_score = round(
            (session.enthusiasm_score * (n - 1) + emotion_result.get('enthusiasm_score', 0)) / n, 2
        )
        session.authority_score = round(
            (session.authority_score * (n - 1) + emotion_result.get('authority_score', 0)) / n, 2
        )
        self.repo.save(session)

        return {
            'success':          True,
            'transcription':    new_text,
            'filler_events':    transcript_result.get('filler_events', []),
            'confidence_score': emotion_result.get('confidence_score', 0),
            'enthusiasm_score': emotion_result.get('enthusiasm_score', 0),
            'authority_score':  emotion_result.get('authority_score', 0),
        }

    def save_posture_event(self, session_id: int, event_type: str,
                           timestamp: float, duration: float = 0.0) -> dict:
        session = self.repo.find_by_id(session_id)
        if not session or session.status != 'active':
            return {'success': False, 'message': 'Session not active', 'code': 400}
        self.repo.add_posture_event(session_id, event_type, timestamp, duration)
        return {'success': True}

    def finish(self, session_id: int, duration_seconds: int) -> dict:
        session = self.repo.find_by_id(session_id)
        if not session:
            return {'success': False, 'message': 'Session not found', 'code': 404}

        session.duration_seconds = duration_seconds
        session.overall_score    = Session.compute_overall(
            session.confidence_score, session.enthusiasm_score, session.authority_score
        )
        session.grade       = Session.compute_grade(session.overall_score)
        session.status      = 'completed'
        session.completed_at= __import__('datetime').datetime.utcnow()
        self.repo.save(session)

        # Generate AI coaching tips
        tips = self.ai.generate_coaching_tips(session.to_dict())
        if tips:
            self.repo.save_coaching_tips(session_id, tips)

        # Update user stats
        user = self.user_repo.find_by_id(session.user_id)
        if user:
            self.user_repo.update_stats_after_session(user, session.confidence_score)

        return {'success': True, 'session': session.to_dict()}

    def get_report(self, session_id: int, user_id: int) -> dict:
        session = self.repo.find_by_id(session_id)
        if not session or session.user_id != user_id:
            return {'success': False, 'message': 'Session not found', 'code': 404}
        report = self.repo.get_full_report(session_id)
        return {'success': True, **report}

    def get_all(self, user_id: int) -> dict:
        sessions = self.repo.find_by_user(user_id)
        return {'success': True, 'sessions': [s.to_dict() for s in sessions]}
