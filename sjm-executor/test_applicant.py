"""Security checks for application inspector; real external form submission is never attempted."""
import unittest
from applicant import checked_url

class SecurityTests(unittest.TestCase):
    def test_official(self):
        url="https://jobs.lever.co/weloglobal/54157634-2cb4-4073-a1e6-4b51f3d411fd/apply"
        self.assertEqual(checked_url(url),url)
    def test_disallowed(self):
        for url in ("http://127.0.0.1:8765/","https://localhost/","http://169.254.169.254/",
                    "https://example.com/","https://jobs.lever.co/internal"):
            with self.subTest(url=url), self.assertRaises(ValueError): checked_url(url)
    def test_embedded_credentials(self):
        with self.assertRaises(ValueError):
            checked_url("https://a@jobs.lever.co/weloglobal/54157634-2cb4-4073-a1e6-4b51f3d411fd/apply")
    def test_no_arbitrary_queries(self):
        with self.assertRaises(ValueError):
            checked_url("https://jobs.ashbyhq.com/other/path")
if __name__=="__main__":unittest.main()
