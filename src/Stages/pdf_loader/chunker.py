"""Chunk berdasarkan budget token BGE-M3; batas teks tetap di antara kata."""

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_TEXT = BASE_DIR / "output/Pedoman PI_cleaned.txt"
OUTPUT_FILE = BASE_DIR / "output/Pedoman PI_chunks_token.json"
TOKENIZER_FILE = BASE_DIR.parents[2] / ".cache/bge-m3/tokenizer.json"
TOKENIZER_MODEL = "BAAI/bge-m3"
TOKENIZER_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"
CHUNK_TOKENS = 480
OVERLAP_TOKENS = 96
MODEL_INPUT_LIMIT = 8192


def split_document(extracted_text: str) -> tuple[str, str]:
    """Pisahkan daftar isi dan isi utama pada heading Pendahuluan pertama."""
    body_heading = re.search(r"(?m)^1\. PENDAHULUAN\s*$", extracted_text)
    if body_heading is None:
        raise ValueError("Batas isi utama '1. PENDAHULUAN' tidak ditemukan.")
    table_of_contents = extracted_text[:body_heading.start()].strip()
    body = extracted_text[body_heading.start():].strip()
    return table_of_contents, body


@lru_cache(maxsize=1)
def load_tokenizer():
    """Baca tokenizer lokal saja; tidak memuat bobot model atau akses internet."""
    from tokenizers import Tokenizer

    if not TOKENIZER_FILE.is_file():
        raise FileNotFoundError(f"Tokenizer belum tersedia: {TOKENIZER_FILE}. Lihat testing/README.md.")
    tokenizer = Tokenizer.from_file(str(TOKENIZER_FILE))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    return tokenizer


def count_tokens(text, tokenizer, special=False):
    """Hitung ID token sebenarnya; special=True menyertakan token pembungkus model."""
    return len(tokenizer.encode(text, add_special_tokens=special).ids)


def tokenizer_identity():
    """Catat digest file aktual agar hasil bisa dilacak ke tokenizer yang dipakai."""
    return {"model": TOKENIZER_MODEL, "revision": TOKENIZER_REVISION,
            "sha256": hashlib.sha256(TOKENIZER_FILE.read_bytes()).hexdigest()}


def chunk_by_tokens(text, tokenizer, budget=CHUNK_TOKENS, overlap=OVERLAP_TOKENS):
    """Penuhi budget dengan kata utuh; overlap adalah maksimum, bukan jumlah pasti.

    Setiap kandidat dihitung ulang dengan tokenizer. Satu kata yang melebihi
    budget menghasilkan error jelas; tidak dipotong diam-diam di tengah Unicode.
    Offset kata lokal berbasis 0, end eksklusif, memungkinkan rekonstruksi pasti.
    """
    if type(budget) is not int or budget <= 0:
        raise ValueError("Budget token harus integer positif.")
    if type(overlap) is not int or not 0 <= overlap < budget:
        raise ValueError("Overlap token harus integer >= 0 dan < budget.")
    words, chunks, start, previous_end = text.split(), [], 0, 0
    while start < len(words):
        end = start
        while end < len(words):
            candidate = " ".join(words[start:end + 1])
            if count_tokens(candidate, tokenizer) > budget:
                break
            end += 1
        if end == start:
            raise ValueError(f"Kata pada offset {start} melebihi budget {budget} token.")
        chunk = " ".join(words[start:end])
        chunks.append({"text": chunk, "word_start": start, "word_end": end,
                       "word_count": end - start,
                       "token_count": count_tokens(chunk, tokenizer),
                       "input_token_count": count_tokens(chunk, tokenizer, special=True),
                       "overlap_tokens_before": count_tokens(" ".join(words[start:previous_end]), tokenizer)
                       if start < previous_end else 0})
        if end == len(words):
            break
        next_start = end
        while next_start > start + 1 and overlap:
            if count_tokens(" ".join(words[next_start - 1:end]), tokenizer) > overlap:
                break
            next_start -= 1
        # Jika overlap menyisakan ruang terlalu kecil untuk kata berikutnya,
        # kurangi overlap sampai chunk berikutnya bisa menambah konten baru.
        while next_start < end and count_tokens(" ".join(words[next_start:end + 1]), tokenizer) > budget:
            next_start += 1
        previous_end, start = end, next_start
    return chunks


def build_records(text, tokenizer, identity):
    """Chunk daftar isi dan isi utama terpisah; offset terhadap sumber penuh."""
    toc, body = split_document(text)
    records, offset = [], 0
    for content_type, section in (("daftar_isi", toc), ("isi_utama", body)):
        for local_index, chunk in enumerate(chunk_by_tokens(section, tokenizer), start=1):
            chunk.update({"chunk_index": len(records) + 1, "section_chunk_index": local_index,
                          "content_type": content_type, "source": INPUT_TEXT.name,
                          "tokenizer": identity, "chunk_token_budget": CHUNK_TOKENS,
                          "overlap_token_budget": OVERLAP_TOKENS})
            chunk["word_start"] += offset
            chunk["word_end"] += offset
            if chunk["input_token_count"] > MODEL_INPUT_LIMIT:
                raise ValueError("Chunk termasuk special tokens melebihi batas input BGE-M3.")
            records.append(chunk)
        offset += len(section.split())
    return records


def main():
    """Baca teks bersih, lakukan chunking token, lalu simpan hasil ke JSON."""
    tokenizer = load_tokenizer()
    records = build_records(INPUT_TEXT.read_text(encoding="utf-8-sig"), tokenizer, tokenizer_identity())
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Selesai: {len(records)} chunk, budget {CHUNK_TOKENS} token, overlap maksimum {OVERLAP_TOKENS} token.")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
