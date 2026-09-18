import json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from pathlib import Path

ROOT = Path(__file__).parent
NVIDIA_URL = 'https://integrate.api.nvidia.com/v1/chat/completions'
MODEL = os.getenv('NVIDIA_MODEL', 'nvidia/llama-3.1-nemotron-70b-instruct')

def load_dotenv():
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text().splitlines():
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                k,v=line.split('=',1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
load_dotenv()

class Handler(BaseHTTPRequestHandler):
    def _json(self, status, data):
        raw=json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path in ('/','/index.html'):
            raw=(ROOT/'index.html').read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
        elif self.path=='/health': self._json(200,{'ok':True,'model':MODEL,'key_configured':bool(os.getenv('NVIDIA_API_KEY'))})
        else: self.send_error(404)
    def do_POST(self):
        if self.path!='/api/chat': self.send_error(404); return
        key=os.getenv('NVIDIA_API_KEY')
        if not key: self._json(503,{'error':'NVIDIA_API_KEY is not configured on the server'}); return
        try:
            n=int(self.headers.get('Content-Length','0')); body=json.loads(self.rfile.read(n))
            topic=body.get('topic','Daily life'); level=body.get('level','Beginner'); messages=body.get('messages',[])[-12:]
            system=f'''You are Fluentia, a friendly English tutor for a Brazilian learner. Topic: {topic}. Level: {level}. Keep the conversation advancing naturally; do not repeat previous questions. Every response must be valid JSON only, with exactly these keys: question_en (one natural next question in English), translation_pt (Brazilian Portuguese translation), options (an array of exactly two objects with en and pt keys). The two options must be natural possible answers to your question, suitable for the learner's level. Correct the learner gently when useful, but keep the focus on conversation. Do not use markdown or code fences.'''
            payload={'model':MODEL,'messages':[{'role':'system','content':system}]+messages,'temperature':0.7,'max_tokens':500,'stream':False}
            req=Request(NVIDIA_URL,data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
            with urlopen(req,timeout=90) as r: result=json.loads(r.read())
            text=result['choices'][0]['message']['content'].strip()
            if text.startswith('```'): text=text.split('```')[1].replace('json','',1).strip()
            answer=json.loads(text)
            if not isinstance(answer.get('options'),list) or len(answer['options'])!=2: raise ValueError('The model did not return two options')
            self._json(200,answer)
        except HTTPError as e:
            self._json(502,{'error':f'NVIDIA request failed ({e.code})'})
        except (URLError,TimeoutError): self._json(504,{'error':'NVIDIA request timed out'})
        except Exception as e:
            self._json(502,{'error':'Could not process the AI response'})
    def log_message(self, fmt, *args): pass

if __name__=='__main__':
    port=int(os.getenv('PORT','8000'))
    print(f'Fluentia server running at http://localhost:{port}')
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
