"""Tahap lanjutan: ekstrak tabel PDF digital menjadi file CSV."""

import csv
from pathlib import Path

import pymupdf


# Ubah nilai berikut sesuai file PDF dan folder output yang ingin digunakan.
INPUT_PDF = Path("input_pdf/LPJ.pdf")
OUTPUT_DIR = Path("output/tables")


def extract_tables(input_pdf: Path, output_dir: Path) -> list[Path]:
    """Mendeteksi tabel pada setiap halaman dan menulis satu CSV per tabel."""
    if not input_pdf.is_file():
        raise FileNotFoundError(f"File PDF tidak ditemukan: {input_pdf}")

    if input_pdf.suffix.lower() != ".pdf":
        raise ValueError("File input harus berformat .pdf")

    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files: list[Path] = []

    with pymupdf.open(input_pdf) as document:
        for page_number, page in enumerate(document, start=1):
            tables = page.find_tables()

            for table_number, table in enumerate(tables.tables, start=1):
                rows = table.extract()
                output_file = output_dir / (
                    f"page_{page_number:03d}_table_{table_number:02d}.csv"
                )

                with output_file.open("w", encoding="utf-8-sig", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerows(rows)

                saved_files.append(output_file)

    return saved_files


def main() -> None:
    """Menjalankan ekstraksi tabel menggunakan konfigurasi di dalam file."""

    try:
        saved_files = extract_tables(INPUT_PDF, OUTPUT_DIR)
    except (FileNotFoundError, ValueError, OSError, RuntimeError) as error:
        raise SystemExit(f"Gagal: {error}") from error

    if not saved_files:
        print("Selesai, tetapi tidak ada tabel yang terdeteksi.")
        return

    print(f"Selesai. {len(saved_files)} tabel disimpan:")
    for saved_file in saved_files:
        print(f"- {saved_file.resolve()}")


if __name__ == "__main__":
    main()