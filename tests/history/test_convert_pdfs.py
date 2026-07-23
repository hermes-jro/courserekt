"""Path-safety tests for PDF conversion output mapping."""

import tempfile
import unittest
from pathlib import Path

from src.history.convert_pdfs import _raw_destination


class ConvertPathTestCase(unittest.TestCase):
    def test_pdf_maps_only_to_sibling_raw_tree(self) -> None:
        with tempfile.TemporaryDirectory(prefix="courserekt-path-test-") as temp:
            source = Path(temp) / "data" / "pdfs" / "2627" / "1" / "round_1.pdf"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"%PDF-test")
            self.assertEqual(
                _raw_destination(source),
                Path(temp).resolve() / "data" / "raw" / "2627" / "1" / "round_1.csv",
            )

    def test_source_outside_data_pdfs_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="courserekt-path-test-") as temp:
            source = Path(temp) / "round_1.pdf"
            source.write_bytes(b"%PDF-test")
            with self.assertRaises(ValueError):
                _raw_destination(source)


if __name__ == "__main__":
    unittest.main()
