#!/usr/bin/env python3
"""SJM Control 360: safely scheduled, persistent, public read-only job queue.

No credentials, applicant data, submissions or third-party writes.
The queue/result files are public; never add private case data.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
QUEUE = HERE / "public_jobs.json"
RESULTS = HERE / "public_results.json"
HOSTS = {"sjm-playwright-executor.onrender.com", "eic.ec.europa.eu", "www.awesomefoundation.org"}
KINDS = {"executor_health", "official_page"}
UTC = dt.timezone.utc

def iso(t):
    return t.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def parse_time(s):
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return dt.datetime.min.replace(tzinfo=UTC)

def validate(job):
    if not isinstance(job, dict) or set(job) != {"id", "kind", "url", "interval_hours"}:
        raise ValueError("Only id, kind, url and interval_hours are allowed (NO private data)")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", job["id"]):
        raise ValueError("Invalid job id")
    if job["kind"] not in KINDS:
        raise ValueError("Only read-only operations are allowed")
    u = urlparse(job["url"])
    if u.scheme != "https" or u.hostname not in HOSTS or u.username or u.password or u.port:
        raise ValueError("URL is not an approved HTTPS endpoint")
    if not isinstance(job["interval_hours"], int) or not 1 <= job["interval_hours"] <= 72:
        raise ValueError("Invalid recurrence")
    if job["kind"] == "executor_health" and (u.hostname != "sjm-playwright-executor.onrender.com" or u.path != "/healthz"):
        raise ValueError("Incorrect executor health path")

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urlparse(newurl)
        if u.scheme != "https" or u.hostname not in HOSTS:
            raise ValueError("Unsafe redirect blocked")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def check_once(job):
    request = urllib.request.Request(job["url"], headers={
        "User-Agent": "SJM-Control360-PublicQueue/1.0 (read-only)",
        "Accept": "application/json,text/html",
    }, method="GET")
    try:
        opener = urllib.request.build_opener(SafeRedirect)
        with opener.open(request, timeout=45) as response:
            body = response.read(32768)
            status = response.status
            resolved = urlparse(response.geturl())
            if resolved.scheme != "https" or resolved.hostname not in HOSTS:
                raise ValueError("Unexpected URL")
        outcome = "checked_ok" if status == 200 else "needs_review"
        details = "Official public page reached; individual eligibility NOT verified"
        if job["kind"] == "executor_health":
            payload = json.loads(body.decode("utf-8"))
            if payload.get("status") != "ready" or payload.get("version") != "application-gated-submit-v4":
                outcome = "needs_review"
                details = "Executor version or ready status differs"
            else:
                details = "Executor HTTP 200, ready; this is NOT a submission test"
        return {"outcome": outcome, "http_status": status,
                "evidence_sha256": hashlib.sha256(body).hexdigest(),
                "detail": details}
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc:
        return {"outcome": "needs_review", "http_status": getattr(exc, "code", None),
                "detail": "Read-only check failed: " + type(exc).__name__}

def check(job):
    """Retry Render free-service cold starts; never hide a persistent failure."""
    if job["kind"] != "executor_health":
        return check_once(job)
    import time
    result = {}
    for attempt in range(4):
        result = check_once(job)
        if result["outcome"] == "checked_ok":
            result["checks_attempted"] = attempt + 1
            return result
        if result.get("http_status") not in (502, 503, 504):
            break
        if attempt < 3:
            time.sleep(12)
    result["checks_attempted"] = attempt + 1
    result["detail"] += "; unavailable after retry" if attempt == 3 else ""
    return result

def run(now=None):
    now = now or dt.datetime.now(UTC)
    jobs = json.loads(QUEUE.read_text(encoding="utf-8"))["jobs"]
    if not isinstance(jobs, list) or len(jobs) > 30:
        raise ValueError("Invalid queue size")
    ids = set()
    for job in jobs:
        validate(job)
        if job["id"] in ids:
            raise ValueError("Duplicate job id")
        ids.add(job["id"])
    if RESULTS.exists():
        state = json.loads(RESULTS.read_text(encoding="utf-8"))
    else:
        state = {"schema_version": 1, "jobs": {}, "last_cycle": None}
    state.setdefault("jobs", {})
    executed = []
    for job in jobs:
        old = state["jobs"].get(job["id"], {})
        if parse_time(old.get("next_due", "")) > now:
            continue
        result = check(job)
        result.update({"checked_utc": iso(now),
                       "next_due": iso(now + dt.timedelta(hours=1 if result["outcome"] != "checked_ok" else job["interval_hours"])),
                       "kind": job["kind"], "url": job["url"],
                       "attempts": old.get("attempts", 0) + 1})
        state["jobs"][job["id"]] = result
        executed.append({"id": job["id"], **result})
    state["last_cycle"] = iso(now)
    state["schema_version"] = 1
    state["jobs"] = {job["id"]: state["jobs"][job["id"]] for job in jobs if job["id"] in state["jobs"]}
    RESULTS.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Simple status sheet for the founder, with verified evidence only.
    safe_count = sum(state["jobs"].get(j["id"], {}).get("outcome") == "checked_ok" for j in jobs)
    lines = [
        "# SJM CONTROL 360 — ESTADO COMPROBADO",
        "",
        "**Última ejecución automática (UTC):** " + iso(now),
        "",
        "**Comprobaciones correctas: " + str(safe_count) + " de " + str(len(jobs)) + "**",
        "",
        "| Control | Resultado | Próxima revisión (UTC) |",
        "|---|---|---|",
    ]
    for job in jobs:
        item = state["jobs"].get(job["id"], {})
        mark = "🟢" if item.get("outcome") == "checked_ok" else "🔴"
        lines.append("| " + job["id"] + " | " + mark + " " + item.get("outcome", "pendiente") +
                     " | " + item.get("next_due", "-") + " |")
    lines.extend([
        "",
        "🟢 = comprobación automática realizada correctamente. 🔴 = fallo o revisión requerida.",
        "",
        "**Importante:** estas comprobaciones verifican páginas oficiales y salud del servidor. "
        "NO son solicitudes de empleo enviadas, aprobaciones, contratos ni prueba de "
        "autonomía integral. No se procesan datos personales ni se firman formularios.",
        "",
        "**Próximo objetivo:** conectar casos autorizados y sus acuses a un ejecutor protegido.",
        "",
        "[Evidencia JSON](public_results.json) · "
        "[Ejecuciones de GitHub Actions](https://github.com/andersonmartinezquiroga-ux/SM-Personal-Trainer/actions)",
        "",
    ])
    (HERE / "ESTADO.md").write_text("\n".join(lines), encoding="utf-8")
    summary = {"checked_now": len(executed), "ok": sum(x["outcome"] == "checked_ok" for x in executed),
               "needs_review": sum(x["outcome"] != "checked_ok" for x in executed),
               "queue_size": len(jobs), "result_file": str(RESULTS)}
    print(json.dumps(summary, ensure_ascii=False))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as file:
            file.write("## SJM CONTROL 360 — Cola automática, SOLO LECTURA\n\n")
            file.write("| Trabajo | Resultado | Fecha UTC |\n|---|---|---|\n")
            for job in jobs:
                s = state["jobs"].get(job["id"], {})
                file.write("| " + job["id"] + " | " + s.get("outcome", "pending") + " | " + s.get("checked_utc", "-") + " |\n")
            file.write("\n**No se envían solicitudes ni datos personales.** Los resultados se guardan como evidencia en JSON.\n")
    return summary

def self_test():
    sample = {"id": "health-test", "kind": "executor_health", "url": "https://sjm-playwright-executor.onrender.com/healthz", "interval_hours": 2}
    validate(sample)
    for change in ({"url": "http://localhost/private"}, {"url": "https://example.com/"}, {"kind": "submit_form"}, {"email": "private@example.com"}):
        bad = dict(sample, **change)
        try:
            validate(bad)
            raise AssertionError("Unsafe queue job was accepted")
        except ValueError:
            pass
    assert parse_time("2026-11-01T00:00:00Z").tzinfo is not None
    print("PASS: allowed hosts, no personal data, HTTPS-only, no submission jobs, UTC parsing")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test() if args.self_test else run()
