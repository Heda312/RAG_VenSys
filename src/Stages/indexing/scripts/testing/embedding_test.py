import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

# 1. Path input JSON
json_path = (
    Path("storages")
    / "outputs"
    / "pdf_sampel_chunks_token.json"
)

# 2. Path output untuk menyimpan hasil embedding
output_path = (
    Path("src")
    / "Stages"
    / "indexing"
    / "scripts"
    / "testing"
    / "reports"
    / "pdf_sampel_embeddings.json"
)

# 3. Load data chunks
if not json_path.is_file():
    raise FileNotFoundError(f"File JSON input tidak ditemukan: {json_path}")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 4. Ambil teks
texts = [item["text"] for item in data if "text" in item]

print(f"📦 Total chunks yang akan di-embed: {len(texts)}")

# 5. Load Model BGE-M3 Native dari Hugging Face
print("⏳ Loading model BGE-M3 Native (sentence-transformers)...")
model = SentenceTransformer("BAAI/bge-m3")

# 6. Generate embedding secara native & batch
print("🚀 Mengomputasi embedding...")
# convert_to_numpy=True/tolist() memastikan output siap di-serialize ke JSON
embeddings = model.encode(
    texts, 
    batch_size=16, 
    show_progress_bar=True, 
    convert_to_numpy=True
)

# 7. Gabungkan teks chunk dengan hasil vektor embedding-nya
output_data = []
for item, embedding in zip(data, embeddings):
    output_data.append(
        {
            "chunk_index": item.get("chunk_index"),
            "text": item.get("text"),
            "embedding": embedding.tolist(),  # Diubah ke List Python biasa biar muat di JSON
        }
    )

# 8. Simpan ke file JSON baru
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"✅ Selesai! Hasil {len(output_data)} embedding disimpan ke: {output_path.resolve()}")


