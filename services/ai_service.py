# backend/services/ai_service.py
from config.settings import Config
import json

_DEFAULTS = {
    'gemini':   'gemini-2.0-flash',
    'deepseek': 'deepseek-chat',
    'xai':      'grok-3',
    'openai':   'gpt-4o',
}

SYSTEM_PROMPT = """You are a professional AI Career Advisor for Talent Bridge app.
Your role is to:
- Help users navigate their career journey with personalised, actionable advice
- Suggest career paths based on their skills, interests, and market trends
- Assist with resume writing, interview preparation, and salary negotiation
- Recommend learning resources, certifications, and skill-building strategies
- Provide insights on job market trends and in-demand skills
- Encourage and motivate users while being honest about challenges

Always be concise, friendly, and practical. Ask clarifying questions when needed.
Format responses with clear sections when covering multiple points."""


class AIService:
    def __init__(self):
        self.provider = Config.AI_PROVIDER.lower()
        self.api_key  = Config.AI_API_KEY
        self.model    = Config.AI_MODEL or _DEFAULTS.get(self.provider, 'gemini-2.0-flash')

    def chat(self, messages, stream=False):
        if self.provider == 'gemini':
            return self._gemini(messages, stream)
        elif self.provider in ('openai', 'deepseek', 'xai'):
            return self._openai_compat(messages, stream)
        else:
            raise ValueError(f'Unsupported AI provider: {self.provider}')

    def _gemini(self, messages, stream):
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=SYSTEM_PROMPT,
        )
        history = []
        last_user_msg = None
        for msg in messages:
            role = 'user' if msg['role'] == 'user' else 'model'
            if msg == messages[-1] and role == 'user':
                last_user_msg = msg['content']
                continue
            history.append({'role': role, 'parts': [msg['content']]})

        chat = model.start_chat(history=history)

        if stream:
            response = chat.send_message(last_user_msg or '', stream=True)
            def _gen():
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            return _gen()
        else:
            response = chat.send_message(last_user_msg or '')
            return response.text

    def _openai_compat(self, messages, stream):
        import urllib.request
        base_urls = {
            'openai':   'https://api.openai.com/v1',
            'deepseek': 'https://api.deepseek.com/v1',
            'xai':      'https://api.x.ai/v1',
        }
        url = f"{base_urls[self.provider]}/chat/completions"
        payload = json.dumps({
            'model': self.model,
            'messages': [{'role': 'system', 'content': SYSTEM_PROMPT}] + messages,
            'stream': stream,
            'temperature': 0.7,
            'max_tokens': 1024,
        }).encode()
        req = urllib.request.Request(
            url, data=payload,
            headers={'Content-Type': 'application/json',
                     'Authorization': f'Bearer {self.api_key}'},
            method='POST',
        )
        if stream:
            def _gen():
                with urllib.request.urlopen(req) as resp:
                    for line in resp:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: ') and line != 'data: [DONE]':
                            try:
                                data = json.loads(line[6:])
                                delta = data['choices'][0]['delta']
                                if 'content' in delta:
                                    yield delta['content']
                            except Exception:
                                pass
            return _gen()
        else:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
            return data['choices'][0]['message']['content']


ai_service = AIService()
