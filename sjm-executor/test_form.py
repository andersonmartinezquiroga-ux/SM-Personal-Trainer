from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  html='''<!doctype html><html><head><title>SJM Executor Test</title></head><body><form action="/submit" method="post"><input name="name"><input name="email"><button type="submit">Enviar</button></form></body></html>'''
  self.send_response(200);self.end_headers();self.wfile.write(html.encode())
 def do_POST(self):
  n=int(self.headers.get('Content-Length','0'))
  if n > 4096:
   self.send_error(413);return
  fields=parse_qs(self.rfile.read(n).decode())
  if self.path != '/submit' or fields.get('name') != ['SJM Test'] or fields.get('email') != ['test@example.invalid']:
   self.send_error(400);return
  self.send_response(200);self.end_headers();self.wfile.write(b'<html><body>RECIBIDO</body></html>')
if __name__=='__main__':HTTPServer(('127.0.0.1',8765),H).serve_forever()
