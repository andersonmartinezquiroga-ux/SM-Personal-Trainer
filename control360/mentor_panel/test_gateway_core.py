"""Offline gateway regression tests; no real users, tokens or external calls."""
import unittest
from gateway_core import (
    AccessDenied, InvalidInput, get_owner_mentor_receipt,
    submit_owner_mentor_text,
)

OWNER = "verified-test-owner-subject"
STRANGER = "other-verified-subject"

def valid_submit(text, key):
    return {
        "status": "queued", "route": "approved_status",
        "result": {"id": 100, "duplicate": False,
                   "private_notes": "never disclose"},
    }

def valid_receipt(key):
    return {
        "found": True, "command_id": 100, "state": "completed",
        "intent": "estado_sistema", "authorization_level": "automatic",
        "evidence_present": True, "evidence_type": "internal_live_status",
        "evidence_digest": "testdigest",
        "result": {"email": "private@example.invalid"},
        "private_notes": "must_not_reach_client",
        "details_exposed": False,
    }

class SecureGatewayTests(unittest.TestCase):
    def submit(self, **overrides):
        kw = dict(verified_subject=OWNER, owner_subject=OWNER,
                  phrase="Dime el estado del sistema",
                  request_key="qa-mentor-gateway-1",
                  submit_to_privileged_sql=valid_submit)
        kw.update(overrides)
        return submit_owner_mentor_text(**kw)

    def receipt(self, **overrides):
        kw = dict(verified_subject=OWNER, owner_subject=OWNER,
                  request_key="qa-mentor-gateway-1",
                  read_privileged_receipt=valid_receipt)
        kw.update(overrides)
        return get_owner_mentor_receipt(**kw)

    def test_owner_submits(self):
        result = self.submit()
        self.assertEqual(result["state"],"queued")
        self.assertFalse(result["finished"])
        self.assertTrue(result["backend_receipt_required"])
        self.assertFalse(result["raw_backend_data_exposed"])

    def test_bad_user_cannot_submit(self):
        with self.assertRaises(AccessDenied):
            self.submit(verified_subject=STRANGER)

    def test_missing_verified_identity_denied(self):
        with self.assertRaises(AccessDenied):
            self.submit(verified_subject=None)

    def test_unconfigured_owner_denied(self):
        with self.assertRaises(AccessDenied):
            self.submit(owner_subject=None)

    def test_client_cannot_gain_access_by_changing_key(self):
        with self.assertRaises(AccessDenied):
            self.receipt(verified_subject=STRANGER,request_key="qa-other-key")

    def test_invalid_key_is_rejected(self):
        with self.assertRaises(InvalidInput):
            self.submit(request_key="../../credentials")

    def test_short_phrase_rejected(self):
        with self.assertRaises(InvalidInput):
            self.submit(phrase="")

    def test_overlong_phrase_rejected(self):
        with self.assertRaises(InvalidInput):
            self.submit(phrase="X"*1001)

    def test_duplicate_remains_duplicate(self):
        def duplicate(text,key):
            return {"route":"approved_status","status":"queued",
                    "result":{"duplicate":True}}
        result=self.submit(submit_to_privileged_sql=duplicate)
        self.assertTrue(result["duplicate"])
        self.assertFalse(result["finished"])

    def test_blocked_backend_not_presented_as_completed(self):
        def blocked(text,key):
            return {"route":"unrecognized","status":"blocked","result":{"executed":False}}
        result=self.submit(submit_to_privileged_sql=blocked)
        self.assertEqual(result["state"],"blocked")
        self.assertTrue(result["finished"])

    def test_unknown_backend_status_fails_closed(self):
        def unknown(text,key):
            return {"route":"approved_status","status":"paid","result":{}}
        result=self.submit(submit_to_privileged_sql=unknown)
        self.assertEqual(result["state"],"blocked")

    def test_receipt_is_sanitized(self):
        result=self.receipt()
        self.assertEqual(result["state"],"completed")
        self.assertFalse(result["details_exposed"])
        self.assertNotIn("result",result)
        self.assertNotIn("private_notes",result)
        self.assertNotIn("email",str(result))

    def test_invalid_receipt_key_rejected_before_db_call(self):
        called=[]
        def db(key):
            called.append(key)
            return valid_receipt(key)
        with self.assertRaises(InvalidInput):
            self.receipt(request_key="bad / key",read_privileged_receipt=db)
        self.assertEqual(called,[])

    def test_unauthorized_never_calls_database(self):
        called=[]
        def db(key):
            called.append(key)
            return valid_receipt(key)
        with self.assertRaises(AccessDenied):
            self.receipt(verified_subject=STRANGER,read_privileged_receipt=db)
        self.assertEqual(called,[])

    def test_invalid_state_receipt_fails_closed(self):
        result=self.receipt(read_privileged_receipt=lambda key:{"state":"wire_transfer_completed"})
        self.assertEqual(result,{"found":False,"state":"blocked","details_exposed":False})

if __name__=="__main__":
    unittest.main()
