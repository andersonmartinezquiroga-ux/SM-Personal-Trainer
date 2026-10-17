"""SJM browser inspector; former one-shot employer submission is closed after Work success."""
import json,os,secrets,threading,tempfile
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from executor import run
from applicant import inspect
from test_form import H

lock=threading.Lock()
DIAGNOSTIC={"local_browser":"on_demand","external_form_read_only":"on_demand","checked_utc":None}

def boot_diagnostic():
    """Execute Chromium in production, but NEVER submit a real external application."""
    from datetime import datetime, timezone
    try:
        with tempfile.TemporaryDirectory() as d:
            a=run("http://127.0.0.1:8765/",d+"/navigation.json")
            b=run("http://127.0.0.1:8765/",d+"/submission.json",submit=True)
        DIAGNOSTIC["local_browser"]="pass" if (a.get("forms",0)>0 and b.get("submitted") and b.get("confirmation")=="RECIBIDO") else "failed"
    except Exception as exc:
        DIAGNOSTIC["local_browser"]="error:"+type(exc).__name__
    try:
        a=inspect("https://jobs.lever.co/weloglobal/54157634-2cb4-4073-a1e6-4b51f3d411fd/apply")
        DIAGNOSTIC["external_form_read_only"]="pass" if (a.get("form_fields_total",0)>0 and not a.get("submitted")) else "failed"
    except Exception as exc:
        DIAGNOSTIC["external_form_read_only"]="error:"+type(exc).__name__
    try:
        y=inspect("https://freelancer.ypai.ai/jobs/openings/data-annotator-co")
        DIAGNOSTIC["ypai_public_form"]="pass" if (y.get("form_fields_total",0)>=5 and y.get("consent_or_captcha_present") and not y.get("submitted")) else "failed"
    except Exception as exc:
        DIAGNOSTIC["ypai_public_form"]="error:"+type(exc).__name__
    DIAGNOSTIC["checked_utc"]=datetime.now(timezone.utc).isoformat()
    print("SJM browser production boot diagnostic",json.dumps(DIAGNOSTIC),flush=True)

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
        presented=self.headers.get("Authorization","")
        tokens=(os.environ.get("EXECUTOR_TOKEN",""),os.environ.get("INSPECTOR_TOKEN",""))
        return any(bool(token) and secrets.compare_digest(presented,"Bearer "+token) for token in tokens)

    def authorized_submission(self):
        token=os.environ.get("SUBMISSION_TOKEN","")
        return bool(token) and secrets.compare_digest(self.headers.get("Authorization",""),"Bearer "+token)

    def do_GET(self):
        if self.path=="/healthz":
            return self.reply(200,{"service":"sjm-playwright-executor","status":"ready",
                "version":"application-inspection-v3","external_submission":"disabled_already_submitted",
                "supabase":"not_connected","diagnostic":DIAGNOSTIC})
        return self.reply(404,{"error":"not_found"})

    def do_POST(self):
        if self.path not in ("/self-test","/jobs/inspect","/jobs/draft","/jobs/submit-ypai"):
            return self.reply(404,{"error":"not_found"})
        if self.path=="/jobs/submit-ypai":
            if not self.authorized_submission(): return self.reply(401,{"error":"unauthorized"})
            # This specific Work-submitted application has already been completed.
            # A stale scheduled job MUST NOT be allowed to submit a duplicate.
            return self.reply(410,{"error":"application_already_submitted","duplicate_prevented":True})
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
    # The cold start must stay lightweight on a free instance. Chromium diagnostics
    # run through separately authorized tests, NOT every boot.
    if os.environ.get("RUN_BOOT_DIAGNOSTIC","0")=="1":
        threading.Thread(target=boot_diagnostic,daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0",int(os.environ.get("PORT","10000"))),API).serve_forever()
