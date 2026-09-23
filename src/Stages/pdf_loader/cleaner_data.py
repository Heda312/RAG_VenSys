import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "output/Pedoman PI.txt"
OUTPUT_FILE = BASE_DIR / "output/Pedoman PI_cleaned.txt"
MIN_SYMBOL_REPEAT = 2


def remove_repeated_symbols(text: str, min_repeat: int = MIN_SYMBOL_REPEAT) -> str:
    """Hapus simbol identik berulang, termasuk jika dipisahkan whitespace."""
    if min_repeat < 2:
        raise ValueError("min_repeat harus bernilai minimal 2.")

    # ([^\w\s]) menangkap satu karakter yang bukan huruf, angka, atau whitespace.
    # (?:\s*\1) meminta simbol yang sama muncul lagi dan mengizinkan adanya
    # spasi, tab, atau baris baru di antara setiap simbol tersebut.
    pattern = rf"([^\w\s])(?:\s*\1){{{min_repeat - 1},}}"
    cleaned_text = text

    while re.search(pattern, cleaned_text, flags=re.UNICODE):
        cleaned_text = re.sub(pattern, " ", cleaned_text, flags=re.UNICODE)

    # Rapikan spasi tanpa menghilangkan batas baris dan paragraf dokumen.
    cleaned_text = re.sub(r"[ \t]+", " ", cleaned_text)
    cleaned_text = re.sub(r" *\n *", "\n", cleaned_text)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    return cleaned_text.strip()


def main() -> None:
    """Baca TXT hasil ekstraksi, bersihkan, lalu simpan sebagai TXT baru."""
    try:
        extracted_text = INPUT_FILE.read_text(encoding="utf-8")
        cleaned_text = remove_repeated_symbols(extracted_text, MIN_SYMBOL_REPEAT)

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text(cleaned_text, encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as error:
        raise SystemExit(f"Gagal: {error}") from error

    print(f"Simbol yang berulang minimal {MIN_SYMBOL_REPEAT} kali telah dihapus.")
    print(f"Hasil disimpan di: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
