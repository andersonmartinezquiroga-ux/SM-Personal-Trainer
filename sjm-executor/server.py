"""Authenticated single-job runner. Only the bundled test form is executable."""
import json, os, secrets, threading, tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from executor import run
from test_form import H

lock = threading.Lock()

class API(BaseHTTPRequestHandler):
    def reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/healthz':
            return self.reply(200, {'service': 'sjm-playwright-executor', 'status': 'ready', 'supabase': 'not_connected'})
        self.reply(404, {'error': 'not_found'})

    def do_POST(self):
        if self.path != '/self-test':
            return self.reply(404, {'error': 'not_found'})
        token = os.environ.get('EXECUTOR_TOKEN', '')
        if not token or not secrets.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token):
            return self.reply(401, {'error': 'unauthorized'})
        if not lock.acquire(blocking=False):
            return self.reply(429, {'error': 'busy'})
        try:
            with tempfile.TemporaryDirectory() as d:
                navigation = run('http://127.0.0.1:8765/', d+'/navigation.json')
                submission = run('http://127.0.0.1:8765/', d+'/submission.json', submit=True)
                self.reply(200, {'navigation': navigation, 'form': submission})
        except Exception as exc:
            print('self-test failed:', type(exc).__name__, flush=True)
            self.reply(500, {'error': 'browser_test_failed'})
        finally:
            lock.release()

if __name__ == '__main__':
    demo = ThreadingHTTPServer(('127.0.0.1', 8765), H)
    threading.Thread(target=demo.serve_forever, daemon=True).start()
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', '10000'))), API).serve_forever()
