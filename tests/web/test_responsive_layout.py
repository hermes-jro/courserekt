"""Source-level regression checks for the responsive application shell."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "src/web/templates/history.html"
STYLES = ROOT / "src/web/static/style.css"


class ResponsiveLayoutTestCase(unittest.TestCase):
    def test_template_exposes_mobile_friendly_structure(self) -> None:
        html = TEMPLATE.read_text(encoding="utf-8")

        self.assertIn('class="app-header"', html)
        self.assertIn('class="controls-card"', html)
        self.assertIn('class="table-scroll"', html)
        self.assertIn('id="table-scroll-hint"', html)
        self.assertIn('aria-describedby="table-scroll-hint"', html)
        self.assertIn('<fieldset', html)
        self.assertIn('<legend', html)
        self.assertNotIn("bootstrap-4.5.2.min.css", html)

    def test_styles_include_touch_and_horizontal_scroll_guards(self) -> None:
        css = STYLES.read_text(encoding="utf-8")

        self.assertIn("@media (max-width: 760px)", css)
        self.assertIn("overflow-x: auto", css)
        self.assertIn("min-height: 44px", css)
        self.assertIn("position: sticky", css)
        self.assertNotIn("height: 100vh", css)


if __name__ == "__main__":
    unittest.main()
