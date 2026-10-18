"""SJM browser executor: public inspection plus explicitly gated role submissions."""
import json, os, secrets, threading, tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from executor import run
from applicant import inspect
from submit_ypai import apply_ypai_role, ROLE_CONFIG
from test_form import H

lock = threading.Lock()
DIAGNOSTIC = {
    "local_browser": "on_demand",
    "external_form_read_only": "on_demand",
    "checked_utc": None,
}

def approved_case_keys():
    raw = os.environ.get("YPAI_APPROVED_CASES", "")
    return {x.strip() for x in raw.split(",") if x.strip()}

def boot_diagnostic():
    """Execute Chromium in production, but NEVER submit a real external application."""
    from datetime import datetime, timezone
    try:
        with tempfile.TemporaryDirectory() as d:
            a = run("http://127.0.0.1:8765/", d + "/navigation.json")
            b = run("http://127.0.0.1:8765/", d + "/submission.json", submit=True)
        DIAGNOSTIC["local_browser"] = (
            "pass" if (a.get("forms", 0) > 0 and b.get("submitted")
                       and b.get("confirmation") == "RECIBIDO") else "failed"
        )
    except Exception as exc:
        DIAGNOSTIC["local_browser"] = "error:" + type(exc).__name__
    try:
        a = inspect("https://jobs.lever.co/weloglobal/54157634-2cb4-4073-a1e6-4b51f3d411fd/apply")
        DIAGNOSTIC["external_form_read_only"] = (
            "pass" if (a.get("form_fields_total", 0) > 0 and not a.get("submitted"))
            else "failed"
        )
    except Exception as exc:
        DIAGNOSTIC["external_form_read_only"] = "error:" + type(exc).__name__
    try:
        y = inspect("https://freelancer.ypai.ai/jobs/openings/text-annotator-co")
        DIAGNOSTIC["ypai_public_form"] = (
            "pass" if (y.get("form_fields_total", 0) >= 5
                       and y.get("consent_or_captcha_present")
                       and not y.get("submitted")) else "failed"
        )
    except Exception as exc:
        DIAGNOSTIC["ypai_public_form"] = "error:" + type(exc).__name__
    DIAGNOSTIC["checked_utc"] = datetime.now(timezone.utc).isoformat()
    print("SJM browser production boot diagnostic", json.dumps(DIAGNOSTIC), flush=True)

class API(BaseHTTPRequestHandler):
    def reply(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        pass

    def authorized(self):
        presented = self.headers.get("Authorization", "")
        tokens = (os.environ.get("EXECUTOR_TOKEN", ""), os.environ.get("INSPECTOR_TOKEN", ""))
        return any(
            bool(token) and secrets.compare_digest(presented, "Bearer " + token)
            for token in tokens
        )

    def authorized_submission(self):
        token = os.environ.get("SUBMISSION_TOKEN", "")
        return bool(token) and secrets.compare_digest(
            self.headers.get("Authorization", ""), "Bearer " + token
        )

    def parse_json(self, max_bytes=12000):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except (ValueError, TypeError):
            raise ValueError("bad_length")
        if length < 0 or length > max_bytes:
            raise ValueError("payload_too_large")
        body = self.rfile.read(length).decode("utf-8")
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError("object_required")
        return data

    def do_GET(self):
        if self.path == "/healthz":
            approvals = approved_case_keys()
            return self.reply(200, {
                "service": "sjm-playwright-executor",
                "status": "ready",
                "version": "application-gated-submit-v4",
                "external_submission": "disabled_without_exact_case_approval",
                "approved_case_count": len(approvals),
                "ypai_role_allowlist": sorted(ROLE_CONFIG),
                "supabase": "queue_driven_external",
                "diagnostic": DIAGNOSTIC,
            })
        return self.reply(404, {"error": "not_found"})

    def do_POST(self):
        known = (
            "/self-test", "/jobs/inspect", "/jobs/draft",
            "/jobs/submit-ypai", "/jobs/submit-ypai-role",
        )
        if self.path not in known:
            return self.reply(404, {"error": "not_found"})

        # Historical Data Annotator endpoint remains permanently closed.
        if self.path == "/jobs/submit-ypai":
            if not self.authorized_submission():
                return self.reply(401, {"error": "unauthorized"})
            return self.reply(
                410,
                {"error": "application_already_submitted", "duplicate_prevented": True},
            )

        if self.path == "/jobs/submit-ypai-role":
            if not self.authorized_submission():
                return self.reply(401, {"error": "unauthorized"})
            try:
                params = self.parse_json()
            except (ValueError, json.JSONDecodeError) as exc:
                return self.reply(400, {"error": "invalid_request", "details": str(exc)[:110]})
            allowed = {
                "role_slug", "case_key", "name", "email", "country",
                "privacy_consent", "contributor_agreement",
            }
            if set(params) - allowed:
                return self.reply(400, {"error": "unsupported_parameters"})
            case_key = params.get("case_key")
            if not isinstance(case_key, str) or case_key not in approved_case_keys():
                return self.reply(403, {
                    "error": "case_not_explicitly_approved",
                    "submitted": False,
                })
            if not lock.acquire(blocking=False):
                return self.reply(429, {"error": "busy"})
            try:
                result = apply_ypai_role(
                    params.get("role_slug"),
                    case_key,
                    params.get("name"),
                    params.get("email"),
                    params.get("country"),
                    params.get("privacy_consent"),
                    params.get("contributor_agreement"),
                )
                return self.reply(200, result)
            except ValueError as exc:
                code = 410 if str(exc) == "application_already_submitted" else 400
                return self.reply(code, {"error": str(exc), "submitted": False})
            except Exception as exc:
                print("role submission runner failed:" + type(exc).__name__, flush=True)
                return self.reply(502, {
                    "error": "browser_execution_failed",
                    "type": type(exc).__name__,
                    "submitted": False,
                })
            finally:
                lock.release()

        if not self.authorized():
            return self.reply(401, {"error": "unauthorized"})
        try:
            params = None
            if self.path != "/self-test":
                params = self.parse_json()
        except (ValueError, json.JSONDecodeError) as exc:
            return self.reply(400, {"error": "invalid_request", "details": str(exc)[:110]})
        if not lock.acquire(blocking=False):
            return self.reply(429, {"error": "busy"})
        try:
            if self.path == "/self-test":
                with tempfile.TemporaryDirectory() as d:
                    navigation = run("http://127.0.0.1:8765/", d + "/navigation.json")
                    submission = run("http://127.0.0.1:8765/", d + "/submission.json", submit=True)
                    return self.reply(200, {"navigation": navigation, "form": submission})
            if not isinstance(params.get("url"), str):
                return self.reply(400, {"error": "url_required"})
            allowed = {"url"} if self.path == "/jobs/inspect" else {"url", "fields"}
            if set(params) - allowed:
                return self.reply(400, {"error": "unsupported_parameters"})
            result = inspect(params["url"], fields=params.get("fields", {}))
            return self.reply(200, result)
        except (ValueError, json.JSONDecodeError) as exc:
            return self.reply(400, {"error": "invalid_request", "details": str(exc)[:110]})
        except Exception as exc:
            print("browser runner failed:" + type(exc).__name__, flush=True)
            return self.reply(502, {"error": "browser_execution_failed", "type": type(exc).__name__})
        finally:
            lock.release()

if __name__ == "__main__":
    demo = ThreadingHTTPServer(("127.0.0.1", 8765), H)
    threading.Thread(target=demo.serve_forever, daemon=True).start()
    if os.environ.get("RUN_BOOT_DIAGNOSTIC", "0") == "1":
        threading.Thread(target=boot_diagnostic, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "10000"))), API).serve_forever()
