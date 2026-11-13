"""Read-only transport ACK tests. No external calls or applications."""
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from api_v2 import readonly_pulse_receipt, read_vetted_public_source, PULSE_VETTED_READS, _NoRedirect

class PulseAckTests(unittest.TestCase):
    good={"slot_start":"2026-11-12T14:30:00Z",
          "focus_key":"computador_donacion_definitiva",
          "signal_count":12,"read_only":True}
    def test_positive_ack_is_transport_only(self):
        result=readonly_pulse_receipt(dict(self.good))
        self.assertTrue(result["received"])
        self.assertFalse(result["external_action_executed"])
        self.assertFalse(result["employer_submission"])
        self.assertEqual(result["slot_start"],self.good["slot_start"])
        self.assertEqual(result["ack_scope"],"signal_transport_only")
        self.assertEqual(len(result["ack_id"]),64)
        self.assertEqual(result["ack_id"],readonly_pulse_receipt(dict(self.good))["ack_id"])

    def test_all_invalid_pulses_rejected(self):
        cases=[
            {**self.good,"read_only":False},
            {**self.good,"signal_count":True},
            {**self.good,"signal_count":65},
            {**self.good,"focus_key":"run_external_applications"},
            {**self.good,"slot_start":"2026-11-12T14:30:00Z?submit=true"},
            {**self.good,"secret":"sensitive"},
            {**self.good,"slot_start":"abc"},
            {},
        ]
        for payload in cases:
            with self.subTest(payload=payload),self.assertRaises(ValueError):
                readonly_pulse_receipt(payload)


    def test_vetted_public_read_is_one_bounded_real_get(self):
        class FakeHTTP:
            status=200
            headers={"Content-Type":"text/html; charset=UTF-8"}
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,size):
                self_size = size
                assert self_size == 8192
                return b"<html><title>Public Rules</title></html>"
        with patch("api_v2.build_opener") as make_opener:
            make_opener.return_value.open.return_value = FakeHTTP()
            outcome=read_vetted_public_source("financiacion_no_reembolsable")
            request=make_opener.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url,PULSE_VETTED_READS["financiacion_no_reembolsable"][1])
            self.assertEqual(request.get_method(),"GET")
            self.assertEqual(make_opener.return_value.open.call_args.kwargs["timeout"],6)
            self.assertIs(make_opener.call_args.args[0],_NoRedirect)
        self.assertEqual(outcome["status"],"read_ok")
        self.assertTrue(outcome["read_only_executed"])
        self.assertEqual(outcome["http_status"],200)
        self.assertFalse(outcome["employer_submission"])
        self.assertEqual(len(outcome["content_sha256"]),64)

    def test_unvetted_focus_never_accesses_an_external_site(self):
        with patch("api_v2.build_opener") as make_opener:
            result=read_vetted_public_source("computador_donacion_definitiva")
            make_opener.assert_not_called()
        self.assertEqual(result["status"],"no_vetted_source")
        self.assertFalse(result["read_only_executed"])

    def test_public_read_http403_is_not_false_success(self):
        with patch("api_v2.build_opener") as make_opener:
            make_opener.return_value.open.side_effect=HTTPError("https://example.org",403,"Forbidden",{},None)
            result=read_vetted_public_source("empleo_y_postulaciones")
        self.assertEqual(result["status"],"http_error")
        self.assertEqual(result["http_status"],403)
        self.assertFalse(result["read_only_executed"])
        self.assertFalse(result["employer_submission"])

if __name__=="__main__":
    unittest.main()
