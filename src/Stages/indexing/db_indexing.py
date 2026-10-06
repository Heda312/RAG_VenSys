import json
from pathlib import Path
import sys
import chromadb

current_file = Path(__file__).resolve()
PROJECT_ROOT = next(
    p for p in current_file.parents if p.name == "RAG_Project"
)

if str(PROJECT_ROOT) not in sys.path:
  sys.path.append(str(PROJECT_ROOT))

from src.embedding_utils import BGEM3EF, MODEL_PATH

DB_FOLDER = (
  PROJECT_ROOT 
  / "storages" 
  / "chroma_db"
)

JSON_PATH = (
    PROJECT_ROOT
    / "storages"
    / "outputs"
    / "vector_embed"
    / "Pedoman PI_embedded.json"
)

if not JSON_PATH.is_file():
  raise FileNotFoundError(f"File JSON input tidak ditemukan: {JSON_PATH}")

with open(JSON_PATH, "r", encoding="utf-8") as f:
  data = json.load(f)

valid_data = [
  item for item in data
  if isinstance(item, dict)
  and isinstance(item.get("text"), str)
  and item["text"].strip()
  and isinstance(item.get("embedding"), list)
]

documents = [item["text"] for item in valid_data]
embeddings = [item["embedding"] for item in valid_data]
ids = [str(item.get("chunk_index", i)) for i, item in enumerate(valid_data)]

client = chromadb.PersistentClient(path=str(DB_FOLDER))
bgem3_ef = BGEM3EF(model_path=MODEL_PATH)

collection = client.get_or_create_collection(
  name = "pedoman_pi",
  embedding_function = bgem3_ef)

collection.upsert(ids=ids, documents=documents, embeddings=embeddings)

count=collection.count()
print(f"Jumlah vector yang tersimpan di ChromaDB: {count}")
