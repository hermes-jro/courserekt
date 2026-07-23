#!/usr/bin/env python3
"""Fail when bundled PDFs contain active content or malformed structure."""

from __future__ import annotations

import argparse
# qpdf is invoked below with a fixed absolute path and an argument list.
import subprocess  # nosec B404
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject

ACTIVE_KEYS = {
    "/AA",
    "/AcroForm",
    "/EmbeddedFile",
    "/EmbeddedFiles",
    "/JavaScript",
    "/JS",
    "/OpenAction",
    "/RichMedia",
    "/XFA",
}
ACTIVE_ACTION_TYPES = {
    "/GoTo3DView",
    "/GoToE",
    "/GoToR",
    "/Hide",
    "/ImportData",
    "/JavaScript",
    "/Launch",
    "/Movie",
    "/Named",
    "/Rendition",
    "/ResetForm",
    "/SetOCGState",
    "/Sound",
    "/SubmitForm",
    "/Trans",
    "/URI",
}


def find_active_content(
    obj: Any,
    path: str,
    seen: set[tuple[int, int]],
    findings: list[str],
) -> None:
    """Recursively inspect the decrypted PDF object graph."""
    if isinstance(obj, IndirectObject):
        identifier = (obj.idnum, obj.generation)
        if identifier in seen:
            return
        seen.add(identifier)
        obj = obj.get_object()

    if isinstance(obj, DictionaryObject):
        for key, value in obj.items():
            key_text = str(key)
            child_path = f"{path}/{key_text.lstrip('/')}"
            if key_text in ACTIVE_KEYS:
                findings.append(child_path)
            if key_text == "/S" and str(value) in ACTIVE_ACTION_TYPES:
                findings.append(f"{child_path}={value}")
            find_active_content(value, child_path, seen, findings)
    elif isinstance(obj, ArrayObject):
        for index, value in enumerate(obj):
            find_active_content(value, f"{path}[{index}]", seen, findings)


def audit_pdf(pdf_path: Path) -> list[str]:
    """Return structural or active-content findings for one PDF."""
    findings: list[str] = []
    # The executable path and argument structure are fixed.
    qpdf = subprocess.run(  # nosec B603
        ["/usr/bin/qpdf", "--check", str(pdf_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if qpdf.returncode not in (0, 3):
        findings.append(f"qpdf failed: {qpdf.stdout.strip()[-500:]}")

    try:
        reader = PdfReader(str(pdf_path), strict=False)
        if reader.is_encrypted and not reader.decrypt(""):
            findings.append("cannot decrypt with the empty password")
            return findings
        find_active_content(reader.trailer, "trailer", set(), findings)
    except Exception as exc:  # noqa: BLE001
        findings.append(f"parser failed: {exc!r}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    pdfs = sorted(root.glob("src/history/**/data/pdfs/**/*.pdf"))
    failures = {
        str(pdf.relative_to(root)): findings
        for pdf in pdfs
        if (findings := audit_pdf(pdf))
    }
    print(f"Audited {len(pdfs)} PDFs.")
    for path, findings in failures.items():
        print(f"FAIL {path}: {'; '.join(findings)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
