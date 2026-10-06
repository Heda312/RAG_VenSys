from pathlib import Path
import chromadb
from chromadb.errors import NotFoundError

current_file = Path(__file__).resolve()
PROJECT_ROOT = next(
    p for p in current_file.parents if p.name == "RAG_Project"
)

DB_FOLDER = (
  PROJECT_ROOT 
  / "storages" 
  / "chroma_db"
)

client = chromadb.PersistentClient(path=str(DB_FOLDER))
collection_name = "pedoman_pi"

try:
  client.delete_collection(name=collection_name)
  print(
      f"Koleksi '{collection_name}' berhasil dihapus dari ChromaDB di"
      f" folder: {DB_FOLDER.resolve()}"
  )
except (NotFoundError, ValueError, Exception) as e:
  print(
      f"Koleksi '{collection_name}' memang tidak ditemukan di"
      f" {DB_FOLDER.resolve()}."
  )