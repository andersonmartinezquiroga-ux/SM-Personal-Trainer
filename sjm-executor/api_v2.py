"""SJM browser executor: public inspection plus explicitly gated role submissions."""
import json, os, secrets, threading, tempfile, re, hashlib
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

PULSE_FOCI = frozenset((
    "computador_donacion_definitiva", "empleo_y_postulaciones",
    "patrocinios", "financiacion_no_reembolsable",
    "clientes_e_ingresos", "alianzas",
))

def readonly_pulse_receipt(data):
    """ACK authenticated transport of a radar pulse, NOT any external action."""
    if not isinstance(data, dict) or set(data) != {"slot_start", "focus_key", "signal_count", "read_only"}:
        raise ValueError("pulse_fields_invalid")
    slot, focus, count = data["slot_start"], data["focus_key"], data["signal_count"]
    if not isinstance(slot, str) or not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:00Z", slot):
        raise ValueError("pulse_slot_invalid")
    if focus not in PULSE_FOCI or type(count) is not int or not 0 <= count <= 64 or data["read_only"] is not True:
        raise ValueError("pulse_policy_invalid")
    checksum = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {
        "received": True, "ack_id": checksum, "slot_start": slot, "focus_key": focus,
        "signal_count": count, "transport": "authenticated_http_post",
        "external_action_executed": False, "employer_submission": False,
        "ack_scope": "signal_transport_only"
    }

class API(BaseHTTPRequestHandler):
    def reply(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        # Structured, secret-free response evidence for Render/Supabase correlation.
        # Never log headers, payloads, query strings, or personal data.
        route = self.path.split("?", 1)[0]
        if route in {"/healthz", "/self-test", "/jobs/inspect", "/jobs/draft", "/jobs/submit-ypai", "/jobs/submit-ypai-role"}:
            # Correlate only a bounded opaque identifier, never a token or request body.
            # The caller must pass the same request_id used in its Supabase ACK.
            raw_id = self.headers.get("X-Request-ID", "")
            request_id = raw_id if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", raw_id) else None
            print(json.dumps({"event": "browser_http_response", "route": route,
                              "status": status, "request_id": request_id,
                              "submitted": False if route in {"/jobs/inspect", "/jobs/draft", "/self-test"} else None}), flush=True)

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

    def do_HEAD(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

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
        if self.path == "/signals/pulse":
            if not self.authorized():
                return self.reply(401, {"error": "unauthorized"})
            try:
                return self.reply(200, readonly_pulse_receipt(self.parse_json(max_bytes=512)))
            except (ValueError, json.JSONDecodeError) as exc:
                return self.reply(400, {"error": "invalid_readonly_pulse", "details": str(exc)[:100]})

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
