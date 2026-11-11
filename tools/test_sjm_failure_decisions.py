#!/usr/bin/env python3
"""Regresión del clasificador usando categorías y frecuencias observadas en
los 20 errores de browser_jobs del 11-nov-2026 (sin información personal)."""
import unittest
from sjm_failure_decisions import Context,decide,summary_decisions

class RealFailureTaxonomyTests(unittest.TestCase):
    def setUp(self):
        self.safe=Context(operation="inspect",source_allowlisted=True,
                          case_active=True,recent_job_count_24h=1,
                          failure_age_minutes=40)
    def test_all_20_historical_error_classes(self):
        samples=(
          [("SJM_QA_CONTROLLED_FAULT_NO_EXTERNAL_TARGET","SYNTHETIC_FAULT")]*8+
          [("HTTP:400,,timeout:false","INVALID_REQUEST")]*3+
          [("human_challenge_detected_no_bypass","HUMAN_CHALLENGE")]*2+
          [("executor_domain_not_approved_http_400_no_submission","ADAPTER_GAP")]*2+
          [("HTTP:200,,timeout:false","DYNAMIC_FORM_UNVERIFIED")]*2+
          [("HTTP:,Timeout of 100000 ms reached. Total time: 100001 ms,timeout:true","TEMPORARY_NETWORK_ERROR")]*2+
          [("public_form_or_listing_not_verified","DYNAMIC_FORM_UNVERIFIED")])
        self.assertEqual(len(samples),20)
        for e,expectation in samples:
            with self.subTest(error=e):
                d=decide(e,self.safe)
                self.assertEqual(d["code"],expectation)
                self.assertIs(d["outbound_submission_allowed"],False)
                self.assertIs(d["real_action_executed"],False)
        aggregate=summary_decisions((err,self.safe) for err,_ in samples)
        self.assertEqual(sum(aggregate.values()),20)

    def test_retry_only_when_safe_readonly_and_exact_conditions(self):
        e="HTTP:,Timeout of 100000 ms reached,timeout:true"
        self.assertTrue(decide(e,self.safe)["automatic_retry_allowed"])
        variations=(
            {"operation":"submit"},
            {"source_allowlisted":False},
            {"case_active":False},
            {"newer_job_exists":True},
            {"known_official_receipt":True},
            {"recent_job_count_24h":3},
            {"failure_age_minutes":10},
            {"failure_age_minutes":1500},
        )
        for change in variations:
            ctx=Context(**{**self.safe.__dict__,**change})
            d=decide(e,ctx)
            self.assertIs(d["automatic_retry_allowed"],False,(change,d))
            self.assertIs(d["outbound_submission_allowed"],False)

    def test_unknown_and_suspected_submission_never_retried(self):
        for err in (
          "unknown error from future provider",
          "HTTP:401,,timeout:false",
          "HTTP:403,,timeout:true",
          "human_challenge_detected_no_bypass",
          "captcha required",
          "unsupported_source",
          "ack_missing; submission outcome unknown",
          "consent required",
          "English form: ability requires verification",
        ):
            with self.subTest(err=err):
                d=decide(err,self.safe)
                self.assertFalse(d["automatic_retry_allowed"],d)
                self.assertFalse(d["outbound_submission_allowed"],d)

    def test_known_receipt_takes_priority_over_any_retry(self):
        ctx=Context(**{**self.safe.__dict__,"known_official_receipt":True})
        for error in ("HTTP:503,,timeout:false","human_challenge",""):
            d=decide(error,ctx)
            self.assertEqual(d["code"],"DO_NOT_DUPLICATE")
            self.assertFalse(d["automatic_retry_allowed"])

    def test_different_errors_have_different_repair_instructions(self):
        codes=[decide(err,self.safe)["code"] for err in (
          "HTTP:400,,timeout:false",
          "HTTP:200,,timeout:false",
          "human_challenge_detected_no_bypass",
          "executor_domain_not_approved_http_400_no_submission",
          "HTTP:,Timeout of 100000 ms reached,timeout:true",
        )]
        self.assertEqual(len(set(codes)),5)

if __name__=="__main__":
    unittest.main()
