"""Read-only transport ACK tests. No external calls or applications."""
import unittest
from api_v2 import readonly_pulse_receipt

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

if __name__=="__main__":
    unittest.main()
