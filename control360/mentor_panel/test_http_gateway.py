"""SJM Mentor HTTP offline integration tests; fake identities and fake database only."""
import io
import json
import unittest
from wsgiref.util import setup_testing_defaults

from http_gateway import MentorHTTPApp

OWNER = "verified-owner-test-subject-123"
STRANGER = "verified-other-user-subject-456"


class HTTPGatewayTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.requests = {}
        self.calls = {"verify": 0, "submit": 0, "receipt": 0}

        def verify(token):
            self.calls["verify"] += 1
            if token == "valid-owner-test-token":
                return OWNER
            if token == "valid-other-test-token":
                return STRANGER
            return None

        def submit(phrase, key):
            self.calls["submit"] += 1
            duplicate = key in self.requests
            self.requests.setdefault(key, {"phrase": phrase, "id": 57, "state": "completed"})
            return {
                "status": "queued", "route": "approved_status",
                "result": {"duplicate": duplicate, "email": "private@example.invalid"},
                "private_data": "never expose",
            }

        def receipt(key):
            self.calls["receipt"] += 1
            if key not in self.requests:
                return {"found": False, "state": "not_found", "details_exposed": False}
            return {
                "found": True, "command_id": self.requests[key]["id"],
                "state": self.requests[key]["state"], "intent": "estado_sistema",
                "authorization_level": "automatic",
                "evidence_present": True, "evidence_type": "internal_live_status",
                "evidence_digest": "fictitious-digest",
                "private_details": "classified", "email": "private@example.invalid",
            }

        self.app = MentorHTTPApp(
            owner_subject=OWNER,
            verify_bearer_token=verify,
            submit_to_privileged_sql=submit,
            read_privileged_receipt=receipt,
        )

    def request(self, method="POST", path="/v1/mentor/commands", token="valid-owner-test-token",
                body=None, content_type="application/json", headers=None):
        if body is None:
            body = {"phrase": "Dime el estado del sistema", "request_key": "qa-owner-request-01"}
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8") if not isinstance(body, bytes) else body
        env = {}
        setup_testing_defaults(env)
        env.update({
            "REQUEST_METHOD": method, "PATH_INFO": path, "CONTENT_LENGTH": str(len(encoded)),
            "CONTENT_TYPE": content_type, "wsgi.input": io.BytesIO(encoded),
        })
        if token is not None:
            env["HTTP_AUTHORIZATION"] = "Bearer " + token
        if headers:
            env.update(headers)
        status_holder = {}

        def start(status, response_headers, exc_info=None):
            status_holder["status"] = status
            status_holder["headers"] = dict(response_headers)

        raw_response = b"".join(self.app(env, start))
        return (
            int(status_holder["status"].split(" ", 1)[0]),
            json.loads(raw_response.decode("utf-8")),
            status_holder["headers"],
        )

    def test_owner_can_submit_fake_command(self):
        status, result, headers = self.request()
        self.assertEqual(status, 202)
        self.assertEqual(result["route"], "approved_status")
        self.assertTrue(result["backend_receipt_required"])
        self.assertNotIn("private_data", result)
        self.assertIn("no-store", headers["Cache-Control"])

    def test_unverified_token_gets_401_before_db(self):
        status, result, _ = self.request(token="forged-json-claim")
        self.assertEqual((status, result["error"]), (401, "authentication_required"))
        self.assertEqual(self.calls["submit"], 0)

    def test_missing_auth_gets_401(self):
        status, _, _ = self.request(token=None)
        self.assertEqual(status, 401)
        self.assertEqual(self.calls["submit"], 0)

    def test_other_verified_identity_gets_403_without_sql(self):
        status, result, _ = self.request(token="valid-other-test-token")
        self.assertEqual((status, result["error"]), (403, "owner_only"))
        self.assertEqual(self.calls["submit"], 0)

    def test_client_supplied_subject_is_not_used_as_identity(self):
        status, result, _ = self.request(token="valid-other-test-token",body={
            "phrase": "Dime el estado del sistema",
            "request_key": "qa-owner-request-01",
            "verified_subject": OWNER,
        })
        self.assertEqual(status, 403)
        self.assertEqual(self.calls["submit"], 0)

    def test_non_json_body_rejected(self):
        status, _, _ = self.request(content_type="text/plain")
        self.assertEqual(status, 415)
        self.assertEqual(self.calls["submit"], 0)

    def test_extra_unexpected_parameters_rejected(self):
        status, _, _ = self.request(body={
            "phrase": "Dime el estado del sistema",
            "request_key": "qa-owner-request-01",
            "amount": 100,
        })
        self.assertEqual(status, 400)
        self.assertEqual(self.calls["submit"], 0)

    def test_garbage_json_rejected(self):
        status, _, _ = self.request(body=b"{wrong")
        self.assertEqual(status, 400)
        self.assertEqual(self.calls["submit"], 0)

    def test_oversized_body_rejected(self):
        status, _, _ = self.request(body=b"x" * 8193)
        self.assertEqual(status, 413)
        self.assertEqual(self.calls["submit"], 0)

    def test_path_and_method_restrictions(self):
        self.assertEqual(self.request(path="/admin/secret")[0], 404)
        self.assertEqual(self.request(method="GET",path="/v1/mentor/commands")[0], 405)
        self.assertEqual(self.request(method="POST",path="/v1/mentor/commands/qa-test")[0], 405)

    def test_owner_receipt_is_sanitized_and_hidden_from_stranger(self):
        self.request()
        path = "/v1/mentor/commands/qa-owner-request-01"
        status, data, headers = self.request("GET",path)
        self.assertEqual(status, 200)
        self.assertEqual(data["state"], "completed")
        self.assertNotIn("private_details", data)
        self.assertNotIn("email", data)
        self.assertIn("nosniff", headers["X-Content-Type-Options"])
        before = self.calls["receipt"]
        self.assertEqual(self.request("GET",path,token="valid-other-test-token")[0], 403)
        self.assertEqual(self.calls["receipt"], before)

    def test_unkown_receipt_gives_not_found(self):
        status, result, _ = self.request("GET","/v1/mentor/commands/qa-unknown-request")
        self.assertEqual(status, 404)
        self.assertEqual(result["state"], "not_found")

    def test_backend_errors_do_not_expose_trace(self):
        def crash(phrase, key):
            raise RuntimeError("secret-password=TEST_DO_NOT_DISCLOSE")
        self.app.submit_to_privileged_sql = crash
        status, result, _ = self.request()
        self.assertEqual(status, 502)
        self.assertNotIn("TEST_DO_NOT_DISCLOSE", str(result))

    def test_fake_duplicate_key_returns_duplicate(self):
        first = self.request()[1]
        second = self.request()[1]
        self.assertFalse(first["duplicate"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(self.calls["submit"], 2)

    def test_invalid_key_rejected_before_sql(self):
        status, data, _ = self.request(body={
            "phrase": "Dime el estado del sistema",
            "request_key": "../../private",
        })
        self.assertEqual(status, 400)
        self.assertEqual(self.calls["submit"], 0)

    def test_cors_not_opened(self):
        headers = self.request(headers={"HTTP_ORIGIN":"https://attacker.invalid"})[2]
        self.assertNotIn("Access-Control-Allow-Origin", headers)


if __name__ == "__main__":
    unittest.main()
