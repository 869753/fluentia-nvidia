import json, os
from flask import Flask, request, jsonify, send_from_directory
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

app = Flask(__name__, static_folder='.', static_url_path='')
NVIDIA_URL = 'https://integrate.api.nvidia.com/v1/chat/completions'
MODEL = os.getenv('NVIDIA_MODEL', 'nvidia/llama-3.1-nemotron-70b-instruct')

@app.get('/')
def home():
    return send_from_directory('.', 'index.html')

@app.post('/api/chat')
def chat():
    key = os.getenv('NVIDIA_API_KEY')
    if not key:
        return jsonify(error='NVIDIA_API_KEY is not configured'), 503
    body = request.get_json(silent=True) or {}
    topic = body.get('topic', 'Daily life')
    level = body.get('level', 'Beginner')
    messages = body.get('messages', [])[-12:]
    system = f'''You are Fluentia, a friendly English tutor for a Brazilian learner. Topic: {topic}. Level: {level}. Keep the conversation advancing naturally; do not repeat previous questions. Every response must be valid JSON only, with exactly these keys: question_en (one natural next question in English), translation_pt (Brazilian Portuguese translation), options (an array of exactly two objects with en and pt keys). The two options must be natural possible answers to your question, suitable for the learner's level. Correct the learner gently when useful, but keep the focus on conversation. Do not use markdown or code fences.'''
    payload = {'model': MODEL, 'messages': [{'role':'system','content':system}] + messages, 'temperature':0.7, 'max_tokens':500, 'stream':False}
    try:
        req = Request(NVIDIA_URL, data=json.dumps(payload).encode(), headers={'Authorization':'Bearer '+key, 'Content-Type':'application/json'})
        with urlopen(req, timeout=90) as response:
            result = json.loads(response.read())
        text = result['choices'][0]['message']['content'].strip()
        if text.startswith('```'):
            text = text.split('```')[1].replace('json','',1).strip()
        answer = json.loads(text)
        if not isinstance(answer.get('options'), list) or len(answer['options']) != 2:
            raise ValueError('invalid options')
        return jsonify(answer)
    except HTTPError as e:
        return jsonify(error=f'NVIDIA request failed: {e.code}'), 502
    except (URLError, TimeoutError):
        return jsonify(error='NVIDIA request timed out'), 504
    except Exception:
        return jsonify(error='Could not process the AI response'), 502
