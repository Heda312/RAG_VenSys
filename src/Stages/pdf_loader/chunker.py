import json
from pathlib import Path
from transformers import AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    PROJECT_ROOT 
    / "storages" 
    / "outputs" 
    / "extraction" 
    / "Pedoman PI_cleaned.txt"
)

OUTPUT_FILE = (
    PROJECT_ROOT 
    / "storages" 
    / "outputs" 
    / "extraction" 
    / "Pedoman PI_chunks.json"
)

TOKENIZER_MODEL = "BAAI/bge-m3" #Model yang paling optimal untuk embedding multilingual. Bisa juga pakai "BAAI/bge-m3-small" untuk versi lebih ringan.
CHUNK_TOKENS = 480
OVERLAP_TOKENS = 96

def main():
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_MODEL)
    raw_text = INPUT_FILE.read_text(encoding="utf-8-sig")
    words = raw_text.split()

    chunks, start = [], 0

    while start < len(words):
        end = start + 1
        while end <= len(words) and len(tokenizer.encode(" ".join(words[start:end]), add_special_tokens=False)) <= CHUNK_TOKENS:
            end += 1
        
        end = max(start + 1, end - 1)  # Minimal 1 kata
        chunk_text = " ".join(words[start:end])

        chunks.append({
            "chunk_index": len(chunks) + 1,
            "text": chunk_text,
            "token_count": len(tokenizer.encode(chunk_text, add_special_tokens=False)),
            "input_token_count": len(tokenizer.encode(chunk_text, add_special_tokens=True)),
            "source": INPUT_FILE.name
        })

        if end >= len(words):
            break

        next_start = end
        while next_start > start + 1 and len(tokenizer.encode(" ".join(words[next_start:end]), add_special_tokens=False)) < OVERLAP_TOKENS:
            next_start -= 1
        
        start = next_start

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Selesai: {len(chunks)} chunk dibuat!")

if __name__ == "__main__":
    main()