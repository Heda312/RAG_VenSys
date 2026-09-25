from pathlib import Path

import pymupdf4llm


# Ubah nilai berikut sesuai file PDF dan format output yang ingin digunakan.
INPUT_PDF = Path("D:\\RAG_Project\\storages\\inputs\\Understanding Deep Learning (Simon J.D. Prince).pdf")
OUTPUT_FILE = Path("D:/RAG_Project/storages/outputs/pdf_sampel.txt")
OUTPUT_FORMAT = "txt"


def extract_text(input_pdf: Path, output_file: Path, output_format: str) -> Path:
    """Membaca PDF digital dan menyimpan teks hasil ekstraksi."""
    
    if not input_pdf.is_file():
        raise FileNotFoundError(f"File PDF tidak ditemukan: {input_pdf}")

    if input_pdf.suffix.lower() != ".pdf":
        raise ValueError("File input harus berformat .pdf")

    # OCR sengaja dimatikan. PDF hasil scan dapat menghasilkan teks kosong.
    if output_format == "txt":
        extracted_text = pymupdf4llm.to_text(
            str(input_pdf),
            use_ocr=False,
            show_progress=True,
        )
    else:
        extracted_text = pymupdf4llm.to_markdown(
            str(input_pdf),
            use_ocr=False,
            show_progress=True,
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(extracted_text, encoding="utf-8")
    return output_file


def main() -> None:
    try:
        saved_file = extract_text(
            input_pdf=INPUT_PDF,
            output_file=OUTPUT_FILE,
            output_format=OUTPUT_FORMAT,
        )
    except (FileNotFoundError, ValueError, OSError, RuntimeError) as error:
        raise SystemExit(f"Gagal: {error}") from error

    print(f"Selesai. Hasil disimpan di: {saved_file.resolve()}")


if __name__ == "__main__":
    main()