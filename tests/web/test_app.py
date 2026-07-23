import unittest
from contextlib import closing

from src.web.app import app


class AppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        # Create a test client to make requests to the app
        self.app = app.test_client()
        app.testing = True

    def tearDown(self) -> None:
        # Clean up any resources after each test case is run
        pass

    def test_homepage(self) -> None:
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"26/27", response.data)
        self.assertIn(b"Round 1", response.data)

    def test_security_headers(self) -> None:
        response = self.app.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn("script-src 'self'", response.headers["Content-Security-Policy"])

    def test_subpath_url_generation(self) -> None:
        response = self.app.get(
            "/",
            base_url="https://agent.jro.sg",
            headers={"X-Forwarded-Prefix": "/courserekt"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"bootstrap-4.5.2.min.css", response.data)
        self.assertIn(b'href="/courserekt/static/style.css?v=8"', response.data)
        self.assertIn(b'action="/courserekt/"', response.data)

    def test_invalid_form_coordinates_are_rejected(self) -> None:
        response = self.app.post(
            "/",
            data={"year": "2627; DROP TABLE x", "semester": "1", "type": "ug"},
        )
        self.assertEqual(response.status_code, 400)

    def test_form_submission(self) -> None:
        data = {
            "year": "2223",
            "semester": "2",
            "type": "gd",
        }
        response = self.app.post("/", data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_serve_pdf(self) -> None:
        with closing(self.app.get("/pdfs/2324/1/ug/round_1.pdf")) as response:
            self.assertEqual(response.status_code, 200)

    def test_serve_latest_pdf(self) -> None:
        with closing(self.app.get("/pdfs/2627/1/ug/round_1.pdf")) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, "application/pdf")

    def test_four_letter_course_suffix_redirect(self) -> None:
        response = self.app.get("/nusmods/LL5009GRSI")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "https://nusmods.com/courses/LL5009GRSI")

    def test_invalid_route(self) -> None:
        response = self.app.get("/invalid_route")
        self.assertEqual(response.status_code, 404)

    def test_invalid_pdf(self) -> None:
        response = self.app.get("/pdfs/2223/3/ug/round_0.pdf")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
