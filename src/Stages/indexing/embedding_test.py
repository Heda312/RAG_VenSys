import json
from pathlib import Path
import sys

current_file = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in current_file.parents if p.name == "RAG_Project")

if str(PROJECT_ROOT) not in sys.path:
  sys.path.append(str(PROJECT_ROOT))

from src.embedding_utils import BGEM3EF, MODEL_PATH

# 3. Path Input & Output
INPUT_FILE = (
    PROJECT_ROOT
    / "storages"
    / "outputs"
    / "text_chunked"
    / "Pedoman PI_chunks.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "storages"
    / "outputs"
    / "vector_embed"
    / "Pedoman PI_embedded000.json"
)

if not INPUT_FILE.is_file():
  raise FileNotFoundError(f"File JSON input tidak ditemukan: {INPUT_FILE}")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
  data = json.load(f)

valid_data = [item for item in data if "text" in item]
texts = [item["text"] for item in valid_data]

print(f"Total chunks yang akan di-embed: {len(texts)}")

print(f"Loading model BGE-M3 dari: {MODEL_PATH}")
embedder = BGEM3EF(model_path=MODEL_PATH)
print("Mengomputasi embedding...")

embeddings = embedder(texts)

output_data = []
for item, embedding in zip(valid_data, embeddings):
  output_data.append({
      "chunk_index": item.get("chunk_index"),
      "text": item.get("text"),
      "embedding": 
        embedding.tolist() 
        if hasattr(embedding, "tolist") 
        else embedding
  })

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
  json.dump(output_data, f, indent=2, ensure_ascii=False)

print(
    f"Selesai! Hasil {len(output_data)} embedding disimpan ke:"
    f" {OUTPUT_FILE.resolve()}"
)