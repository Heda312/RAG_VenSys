from pathlib import Path
import pymupdf4llm

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_PDF = (
    PROJECT_ROOT 
    / "storages" 
    / "inputs" 
    / "Pedoman PI.pdf"
)
OUTPUT_FILE = (
    PROJECT_ROOT 
    / "storages" 
    / "outputs" 
    / "extraction" 
    / "Pedoman PI.txt"
)

def main() -> None:
    text = pymupdf4llm.to_text(str(INPUT_PDF), use_ocr=False, show_progress=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(text if isinstance(text, str) else str(text), encoding="utf-8")
    print(f"Teks tersimpan di: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()