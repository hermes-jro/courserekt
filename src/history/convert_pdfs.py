import argparse
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from tabula.io import convert_into_by_batch

from lib.PdfCsvMonitorer import PdfCsvMonitorer

from . import logger


def _raw_destination(pdf_file: Path) -> Path:
    """Map a report beneath data/pdfs to the matching safe data/raw path."""
    source = pdf_file.resolve(strict=True)
    if source.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, got {source}")

    parts = source.parts
    markers = [
        index
        for index in range(len(parts) - 1)
        if parts[index:index + 2] == ("data", "pdfs")
    ]
    if len(markers) != 1:
        raise ValueError(f"PDF is not under exactly one data/pdfs directory: {source}")

    data_index = markers[0]
    raw_root = Path(*parts[:data_index + 1], "raw").resolve()
    destination = Path(
        *parts[:data_index + 1],
        "raw",
        *parts[data_index + 2:],
    ).with_suffix(".csv").resolve()
    destination.relative_to(raw_root)
    return destination


def convert(pdf_files: list[str]) -> None:
    """Convert NUS PDF reports into raw CSV files with Tabula."""
    logger.debug("convert invoked with arguments: %s", pdf_files)

    # Use opaque temporary names and an explicit mapping. Decoding a source path
    # from an output filename would allow delimiter-based path traversal.
    with TemporaryDirectory(prefix="courserekt-pdfs-") as tmp_directory:
        tmp_path = Path(tmp_directory)
        destinations: dict[str, Path] = {}
        for index, pdf_file in enumerate(pdf_files):
            source = Path(pdf_file).resolve(strict=True)
            temporary_stem = f"report-{index:04d}"
            destinations[temporary_stem] = _raw_destination(source)
            shutil.copy2(source, tmp_path / f"{temporary_stem}.pdf")

        monitorer = PdfCsvMonitorer(tmp_directory)
        monitorer.start()
        try:
            convert_into_by_batch(
                tmp_directory,
                output_format="csv",
                pages="all",
                lattice=True,
                silent=True,
            )
        finally:
            monitorer.stop()

        for temporary_stem, destination in destinations.items():
            generated_csv = tmp_path / f"{temporary_stem}.csv"
            if not generated_csv.is_file():
                raise FileNotFoundError(
                    f"Tabula did not generate the expected output {generated_csv.name}"
                )
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(generated_csv, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert PDFs to CSV")
    parser.add_argument("pdf_files", nargs="+", help="List of PDF files to convert")
    args = parser.parse_args()
    convert(args.pdf_files)


if __name__ == "__main__":
    main()
