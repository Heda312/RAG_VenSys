import json
from pathlib import Path
import ollama

# 1. Path input JSON
json_path = (
    Path("src")
    / "Stages"
    / "1_pdf_loader"
    / "output"
    / "Pedoman PI_chunks_token.json"
)

# 2. Path output untuk menyimpan hasil embedding (akan dibuat di folder yang sama)
output_path = (
    Path("src")
    / "Stages"
    / "1_pdf_loader"
    / "testing"
    / "reports"
    / "Pedoman PI_embeddings.json"
)

# 3. Load data chunks
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 4. Ambil teks
texts = [item["text"] for item in data if "text" in item]

# 5. Process embedding via Ollama
batch = ollama.embed(model="bge-m3:latest", input=texts)

# 6. Gabungkan teks chunk dengan hasil vektor embedding-nya
output_data = []
for item, embedding in zip(data, batch["embeddings"]):
    output_data.append(
        {
            "chunk_index": item.get("chunk_index"),
            "text": item.get("text"),
            "embedding": embedding,  # Array berisi angka-angka vektor
        }
    )

# 7. Simpan ke file JSON baru
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"Selesai! Hasil embedding disimpan ke: {output_path}")