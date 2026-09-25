import json
from functools import lru_cache
from pathlib import Path
from transformers import AutoTokenizer

# --- PATH DINAMIS / UNIVERSAL ---
INPUT_TEXT = Path("D:/RAG_Project/storages/outputs/pdf_sampel_cleaned.txt")
OUTPUT_FILE = Path(
    "D:/RAG_Project/storages/outputs/pdf_sampel_chunks_token.json"
)

TOKENIZER_MODEL = "BAAI/bge-m3"
TOKENIZER_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"
CHUNK_TOKENS = 480
OVERLAP_TOKENS = 96
MODEL_INPUT_LIMIT = 8192


@lru_cache(maxsize=1)
def load_tokenizer():
    """Download & load tokenizer BGE-M3 otomatis via Hugging Face."""
    print(f"Loading tokenizer {TOKENIZER_MODEL} dari Hugging Face...")
    tokenizer = AutoTokenizer.from_pretrained(
        TOKENIZER_MODEL, revision=TOKENIZER_REVISION
    )
    return tokenizer


def count_tokens(text: str, tokenizer, special: bool = False) -> int:
    """Hitung jumlah token sebenarnya."""
    if not text:
        return 0
    return len(tokenizer.encode(text, add_special_tokens=special))


def tokenizer_identity():
    """Metainfo identitas tokenizer."""
    return {
        "model": TOKENIZER_MODEL,
        "revision": TOKENIZER_REVISION,
        "type": "HuggingFace AutoTokenizer",
    }


def chunk_by_tokens_general(
    text: str, tokenizer, budget=CHUNK_TOKENS, overlap=OVERLAP_TOKENS
) -> list[dict]:
    """Sistem Chunking Universal:

    Menerima teks APAPUN dari awal sampai akhir, memotong secara presisi berdasarkan
    budget token dengan batas kata utuh.
    """
    if not isinstance(budget, int) or budget <= 0:
        raise ValueError("Budget token harus integer positif.")
    if not isinstance(overlap, int) or not (0 <= overlap < budget):
        raise ValueError("Overlap token harus integer >= 0 dan < budget.")

    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    previous_end = 0

    while start < len(words):
        end = start
        # Cari batas maksimum kata yang muat di dalam budget token
        while end < len(words):
            candidate = " ".join(words[start : end + 1])
            if count_tokens(candidate, tokenizer) > budget:
                break
            end += 1

        # Error handling jika ada 1 kata raksasa yang melebih budget sendirian
        if end == start:
            word_over = words[start][:30] + "..."
            print(
                f"[WARNING] Kata pada offset {start} ('{word_over}') melebihi budget {budget} token. Dipaksa masuk 1 kata."
            )
            end = start + 1

        chunk_text = " ".join(words[start:end])
        token_count = count_tokens(chunk_text, tokenizer)
        input_token_count = count_tokens(
            chunk_text, tokenizer, special=True
        )

        if input_token_count > MODEL_INPUT_LIMIT:
            raise ValueError(
                f"Chunk ke-{len(chunks)+1} melebihi batas input BGE-M3 ({MODEL_INPUT_LIMIT} token)."
            )

        # Susun data chunk
        chunks.append(
            {
                "chunk_index": len(chunks) + 1,
                "text": chunk_text,
                "word_start": start,
                "word_end": end,
                "word_count": end - start,
                "token_count": token_count,
                "input_token_count": input_token_count,
                "overlap_tokens_before": (
                    count_tokens(
                        " ".join(words[start:previous_end]), tokenizer
                    )
                    if start < previous_end
                    else 0
                ),
            }
        )

        if end == len(words):
            break

        # Hitung titik awal (start) berikutnya berdasarkan overlap token
        next_start = end
        while next_start > start + 1 and overlap:
            if (
                count_tokens(" ".join(words[next_start - 1 : end]), tokenizer)
                > overlap
            ):
                break
            next_start -= 1

        while (
            next_start < end
            and count_tokens(" ".join(words[next_start:end]), tokenizer)
            > budget
        ):
            next_start += 1

        previous_end = end
        start = next_start

    return chunks


def build_records(text: str, tokenizer, identity: dict):
    """Membungkus hasil chunking universal dengan metadata standar RAG."""
    chunks = chunk_by_tokens_general(text, tokenizer)

    records = []
    for chunk in chunks:
        chunk.update(
            {
                "source": INPUT_TEXT.name,
                "tokenizer": identity,
                "chunk_token_budget": CHUNK_TOKENS,
                "overlap_token_budget": OVERLAP_TOKENS,
            }
        )
        records.append(chunk)

    return records


def main():
    """Baca teks bersih apa saja, lakukan chunking universal, lalu simpan hasil ke JSON."""
    if not INPUT_TEXT.is_file():
        raise FileNotFoundError(f"File input tidak ditemukan: {INPUT_TEXT}")

    tokenizer = load_tokenizer()
    raw_text = INPUT_TEXT.read_text(encoding="utf-8-sig")

    print(
        f"Mulai chunking teks ({len(raw_text.split())} kata) secara dinamis..."
    )
    records = build_records(raw_text, tokenizer, tokenizer_identity())

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        f"✅ Selesai: {len(records)} chunk berhasil dibuat tanpa penanda kaku!"
    )
    print(f"📁 Hasil disimpan di: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()