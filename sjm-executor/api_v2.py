"""SJM authenticated browser executor. External submit is prohibited until case-specific review."""
import json,os,secrets,threading,tempfile
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from executor import run
from applicant import inspect
from test_form import H

lock=threading.Lock()

class API(BaseHTTPRequestHandler):
    def reply(self,status,body):
        data=json.dumps(body,ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self,format,*args):
        # No access logs with user data or query parameters.
        pass

    def authorized(self):
        token=os.environ.get("EXECUTOR_TOKEN","")
        return bool(token) and secrets.compare_digest(self.headers.get("Authorization",""),"Bearer "+token)

    def do_GET(self):
        if self.path=="/healthz":
            return self.reply(200,{"service":"sjm-playwright-executor","status":"ready",
                "version":"application-inspection-v1","external_submission":"disabled",
                "supabase":"not_connected"})
        return self.reply(404,{"error":"not_found"})

    def do_POST(self):
        if self.path not in ("/self-test","/jobs/inspect","/jobs/draft"):
            return self.reply(404,{"error":"not_found"})
        if not self.authorized(): return self.reply(401,{"error":"unauthorized"})
        try:
            length=int(self.headers.get("Content-Length","0"))
        except (ValueError,TypeError):
            return self.reply(400,{"error":"bad_length"})
        if length<0 or length>12000: return self.reply(413,{"error":"payload_too_large"})
        if not lock.acquire(blocking=False): return self.reply(429,{"error":"busy"})
        try:
            if self.path=="/self-test":
                with tempfile.TemporaryDirectory() as d:
                    navigation=run("http://127.0.0.1:8765/",d+"/navigation.json")
                    submission=run("http://127.0.0.1:8765/",d+"/submission.json",submit=True)
                    return self.reply(200,{"navigation":navigation,"form":submission})
            params=json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(params,dict) or not isinstance(params.get("url"),str):
                return self.reply(400,{"error":"url_required"})
            allowed={"url"} if self.path=="/jobs/inspect" else {"url","fields"}
            if set(params)-allowed: return self.reply(400,{"error":"unsupported_parameters"})
            result=inspect(params["url"],fields=params.get("fields",{}))
            return self.reply(200,result)
        except (ValueError,json.JSONDecodeError) as exc:
            return self.reply(400,{"error":"invalid_request","details":str(exc)[:110]})
        except Exception as exc:
            print("browser runner failed:"+type(exc).__name__,flush=True)
            return self.reply(502,{"error":"browser_execution_failed","type":type(exc).__name__})
        finally:lock.release()

if __name__=="__main__":
    demo=ThreadingHTTPServer(("127.0.0.1",8765),H)
    threading.Thread(target=demo.serve_forever,daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0",int(os.environ.get("PORT","10000"))),API).serve_forever()
