#!/usr/bin/env python3
"""SJM CONTROL 360 + KAIROS: maniqui de pruebas (100% SIMULADO).

Cero internet, cero credenciales, cero envios, cero cambios de produccion.
Exito en esta prueba NO significa que las integraciones reales esten validadas.
"""
import hashlib
import json
import time

STATIONS = (
    "Objetivo", "Busqueda", "Captura", "Autenticidad/vigencia",
    "Duplicados", "Elegibilidad", "Prioridad", "Preparacion",
    "Calidad/seguridad/autorizacion", "Ejecucion", "Comprobacion",
    "Registro", "Seguimiento/respuesta", "Cierre/aprendizaje/aviso"
)

class Factory:
    def __init__(self):
        self.seen = set()
        self.simulated_outbox = []
        self.simulated_audit = []

    def run(self, case, fault=None):
        """case is fictional; fault injects a failure at a given station (1-14)."""
        start = time.monotonic()
        state = {"real_submission": False, "real_phone_delivery": False,
                 "official_receipt": None, "virtual_day": 0}
        report = {"id": case["id"], "status": "SIMULATION_PASS",
                  "steps": [], "blocking_station": None,
                  "classification": "SYNTHETIC_ONLY"}
        try:
            for number, label in enumerate(STATIONS, 1):
                if number == fault:
                    raise ValueError("INJECTED_FAILURE")
                if number == 1:
                    assert case.get("project") and case.get("region") and case.get("goal"), "MISSING_OBJECTIVE"
                    evidence = case["goal"]
                elif number == 2:
                    assert case.get("source", "").startswith("mock://"), "ONLY_FICTIONAL_SOURCES"
                    evidence = "Fictional search result"
                elif number == 3:
                    state["source"] = case["source"]
                    state["fingerprint"] = hashlib.sha256(case["source"].encode()).hexdigest()[:16]
                    evidence = "Captured synthetic source"
                elif number == 4:
                    assert state["source"].startswith("mock://"), "SOURCE_NOT_ISOLATED"
                    evidence = "Mock source checked"
                elif number == 5:
                    assert state["fingerprint"] not in self.seen, "DUPLICATE"
                    self.seen.add(state["fingerprint"])
                    evidence = "New synthetic item"
                elif number == 6:
                    assert case.get("eligible", True) and case.get("no_fee", True), "INELIGIBLE"
                    evidence = "Fictional criteria met"
                elif number == 7:
                    state["priority"] = "HIGH"
                    evidence = "HIGH"
                elif number == 8:
                    state["draft"] = "TEST ONLY / DO NOT SEND: " + case["goal"]
                    evidence = "Synthetic draft"
                elif number == 9:
                    assert case.get("approval", True), "NO_APPROVAL"
                    assert "DO NOT SEND" in state["draft"], "DRAFT_UNSAFE"
                    evidence = "Synthetic approval, no personal data"
                elif number == 10:
                    self.simulated_outbox.append({"id": case["id"],
                                                  "destination": "mock://outbox",
                                                  "real": False})
                    evidence = "Intercepted, no real network call"
                elif number == 11:
                    state["ack"] = "SIM-ACK-" + state["fingerprint"]
                    assert state["ack"].startswith("SIM-ACK"), "INVALID_MOCK_ACK"
                    evidence = state["ack"]
                elif number == 12:
                    self.simulated_audit.append({"id": case["id"], "ack": state["ack"]})
                    evidence = "Synthetic audit event"
                elif number == 13:
                    state["virtual_day"] = case.get("days", 19)
                    state["response"] = case.get("response", "interested")
                    assert state["virtual_day"] >= 0, "INVALID_TIME_SKIP"
                    evidence = "Virtual time skipped: " + str(state["virtual_day"]) + " days"
                else:
                    assert state["response"] in ("interested", "rejected", "no_response"), "BAD_RESPONSE"
                    assert not state["real_submission"] and not state["real_phone_delivery"]
                    assert state["official_receipt"] is None
                    evidence = "Fictional closure and notification only"
                report["steps"].append({"number": number, "station": label,
                                        "result": "PASS", "evidence": evidence,
                                        "proof": "SIMULATED"})
        except (AssertionError, ValueError) as exc:
            report["status"] = "SIMULATION_BLOCKED"
            report["blocking_station"] = len(report["steps"]) + 1
            report["steps"].append({"number": report["blocking_station"],
                                    "station": STATIONS[report["blocking_station"] - 1],
                                    "result": "FAIL", "evidence": str(exc),
                                    "proof": "SIMULATED"})
        report["duration_ms"] = round((time.monotonic() - start) * 1000, 3)
        report["real_submission"] = False
        report["real_phone_delivery"] = False
        report["official_receipt"] = None
        report["virtual_days"] = state["virtual_day"]
        return report

def run_suite():
    fixture = {"id": "LAB-001", "project": "SJM-360", "region": "LATAM",
               "goal": "Fictional partnership", "source": "mock://company/example",
               "days": 19, "approval": True, "no_fee": True}
    factory = Factory()
    good = factory.run(fixture)
    dup = factory.run(dict(fixture, id="LAB-DUPLICATE"))
    fee = Factory().run(dict(fixture, id="LAB-FEE", no_fee=False))
    approval = Factory().run(dict(fixture, id="LAB-CONSENT", approval=False))
    injections = [Factory().run(dict(fixture, id="LAB-FAULT-" + str(i)), fault=i)
                  for i in (10, 11, 12, 13)]
    reports = [good, dup, fee, approval] + injections
    assert len(good["steps"]) == 14 and good["status"] == "SIMULATION_PASS"
    assert [x["blocking_station"] for x in reports[1:]] == [5, 6, 9, 10, 11, 12, 13]
    assert all(x["real_submission"] is False and x["real_phone_delivery"] is False
               and x["official_receipt"] is None for x in reports)
    return {"tool": "SJM_FACTORY_CANARY_V1", "label": "SIMULATION_ONLY",
            "stations": 14, "cases": len(reports),
            "full_path_passes": sum(x["status"] == "SIMULATION_PASS" for x in reports),
            "blocked_as_expected": sum(x["status"] == "SIMULATION_BLOCKED" for x in reports),
            "real_end_to_end_verified": False, "results": reports}

if __name__ == "__main__":
    result = run_suite()
    print(json.dumps(result, ensure_ascii=False, indent=2))
