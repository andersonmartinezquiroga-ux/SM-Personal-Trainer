"""End-to-end *loopback-only* HTTP proof for SJM Mentor gateway.

This uses ephemeral port 127.0.0.1, fake tokens and fake backend; it NEVER
exposes the service publicly, writes production data or accesses the Internet.
"""
import json
import threading
import unittest
import urllib.error
import urllib.request
from wsgiref.simple_server import make_server, WSGIRequestHandler

from http_gateway import MentorHTTPApp

OWNER = "fake-owner-signed-session-subject"
OTHER = "other-fake-authenticated-subject"


class _QuietHandler(WSGIRequestHandler):
    def log_message(self, fmt, *args):
        pass


class LocalHTTPWireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.submissions = {}
        cls.calls = {"submit": 0, "receipt": 0}

        def verify(token):
            return {"fixture_owner": OWNER, "fixture_other": OTHER}.get(token)

        def submit(phrase, key):
            cls.calls["submit"] += 1
            duplicate = key in cls.submissions
            cls.submissions.setdefault(key, {"phrase": phrase, "status": "completed"})
            return {"status": "queued", "route": "approved_status",
                    "result": {"id": 42, "duplicate": duplicate,
                               "private_data": "must-not-leak"}}

        def receipt(key):
            cls.calls["receipt"] += 1
            if key not in cls.submissions:
                return {"found": False, "state": "not_found", "details_exposed": False}
            return {
                "found": True, "command_id": 42, "state": "completed",
                "authorization_level": "automatic", "intent": "estado_sistema",
                "evidence_present": True, "evidence_type": "mock_status",
                "evidence_digest": "not_real",
                "secret": "private", "result": {"email": "notreal@example.invalid"},
            }

        app = MentorHTTPApp(
            owner_subject=OWNER, verify_bearer_token=verify,
            submit_to_privileged_sql=submit, read_privileged_receipt=receipt,
        )
        cls.server = make_server("127.0.0.1", 0, app, handler_class=_QuietHandler)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def send(self, method, path, token=None, body=None):
        headers = {}
        if token:
            headers["Authorization"] = "Bearer " + token
        if body is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base + path, data=body, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as resp:
                return resp.status, json.load(resp), dict(resp.headers)
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read()), dict(err.headers)

    def test_01_anonymous_http_request_is_401(self):
        status, _, _ = self.send("POST", "/v1/mentor/commands",
                                 body={"phrase": "Informe del sistema", "request_key": "qa-wire-101"})
        self.assertEqual(status, 401)

    def test_02_other_user_is_403(self):
        status, _, _ = self.send("POST", "/v1/mentor/commands", token="fixture_other",
                                 body={"phrase": "Informe del sistema", "request_key": "qa-wire-102"})
        self.assertEqual(status, 403)

    def test_03_owner_can_queue_mock_command(self):
        status, result, headers = self.send("POST", "/v1/mentor/commands", token="fixture_owner",
            body={"phrase": "Dime el estado del sistema", "request_key": "qa-wire-103"})
        self.assertEqual(status, 202)
        self.assertEqual(result["state"], "queued")
        self.assertNotIn("private_data", str(result))
        self.assertIn("no-store", headers["Cache-Control"])

    def test_04_owner_gets_safe_finished_receipt(self):
        self.send("POST", "/v1/mentor/commands", token="fixture_owner",
                  body={"phrase": "Dime el estado del sistema", "request_key": "qa-wire-104"})
        status, result, _ = self.send("GET", "/v1/mentor/commands/qa-wire-104", token="fixture_owner")
        self.assertEqual(status, 200)
        self.assertEqual(result["state"], "completed")
        self.assertTrue(result["evidence_present"])
        self.assertNotIn("notreal@example.invalid", str(result))
        self.assertNotIn("private", str(result))

    def test_05_same_request_id_detects_duplicate(self):
        key = "qa-wire-105"
        body = {"phrase": "Dime el estado del sistema", "request_key": key}
        status, first, _ = self.send("POST", "/v1/mentor/commands", token="fixture_owner", body=body)
        status2, second, _ = self.send("POST", "/v1/mentor/commands", token="fixture_owner", body=body)
        self.assertEqual((status, status2), (202, 202))
        self.assertFalse(first["duplicate"])
        self.assertTrue(second["duplicate"])

    def test_06_other_cannot_read_owner_receipt(self):
        key = "qa-wire-106"
        self.send("POST", "/v1/mentor/commands", token="fixture_owner",
                  body={"phrase": "Dime el estado del sistema", "request_key": key})
        count = self.calls["receipt"]
        status, _, _ = self.send("GET", "/v1/mentor/commands/"+key, token="fixture_other")
        self.assertEqual(status, 403)
        self.assertEqual(self.calls["receipt"], count)


if __name__ == "__main__":
    unittest.main()
