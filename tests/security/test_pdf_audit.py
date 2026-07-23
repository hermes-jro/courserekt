"""Security regression tests for bundled PDF validation."""

import shutil
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, TextStringObject

from scripts.audit_pdfs import audit_pdf


class PdfAuditTestCase(unittest.TestCase):
    def _write_pdf(self, active: bool) -> Path:
        directory = Path(tempfile.mkdtemp(prefix="courserekt-pdf-test-"))
        output = directory / "fixture.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        if active:
            writer._root_object[NameObject("/A")] = DictionaryObject({
                NameObject("/S"): NameObject("/Launch"),
                NameObject("/F"): TextStringObject("payload"),
            })
        with output.open("wb") as stream:
            writer.write(stream)
        self.addCleanup(shutil.rmtree, directory, True)
        return output

    def test_safe_pdf_passes(self) -> None:
        self.assertEqual(audit_pdf(self._write_pdf(active=False)), [])

    def test_action_type_value_is_detected(self) -> None:
        findings = audit_pdf(self._write_pdf(active=True))
        self.assertTrue(any("/S=/Launch" in finding for finding in findings))


if __name__ == "__main__":
    unittest.main()
