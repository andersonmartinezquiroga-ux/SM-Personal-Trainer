#!/usr/bin/env python3
"""Prueba de límites REALES del servicio publicado, sin credenciales ni envíos.

Una autorización 401 prueba que el servidor remoto recibe la solicitud y
no libera acceso anónimo; NO prueba un flujo de candidatura completo.
"""
import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = "https://sjm-control-360.floot.app"
TESTS = [
    ("panel_privado_anon", "/_api/sjm-panel-8/status", "GET", None),
    ("poll_android_anon", "/_api/kairos/phone_command_poll", "GET", None),
    ("brain_anon", "/_api/kairos/brain_command", "POST",
     '{"action":"execute","instruction":"KAIROS abre Gmail"}'.encode('utf-8')),
]
def main():
    results = []
    for name, route, method, body in TESTS:
        started = time.monotonic()
        request = Request(BASE + route, data=body, method=method,
                          headers={"Accept": "application/json",
                                   "Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=8) as response:
                status = response.status
        except HTTPError as exc:
            status = exc.code
        except (URLError, TimeoutError) as exc:
            status = "unavailable"
        results.append({"test": name, "http_status": status,
                        "latency_ms": round((time.monotonic()-started)*1000, 1),
                        "expected": "401", "passed": status == 401})
    result = {"scope": "PUBLISHED_FLOOT_REAL_AUTH_BOUNDARY", "real_network": True,
              "real_application_submission": False, "real_phone_ack": False,
              "scenarios": len(results), "results": results}
    print(json.dumps(result, indent=2))
    # Fall loudly if auth is missing or endpoint unreachable; never say success by guessing.
    if not all(x["passed"] for x in results):
        raise SystemExit("Unverified or unauthorized live boundary")
if __name__ == "__main__":
    main()
