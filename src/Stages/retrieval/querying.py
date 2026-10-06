from pathlib import Path
import sys

current_file = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in current_file.parents if p.name == "RAG_Project")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import chromadb
from src.embedding_utils import BGEM3EF, MODEL_PATH


DB_FOLDER = PROJECT_ROOT / "storages" / "chroma_db"


def retrieve_context(question: str, n_results: int = 5) -> str:
    client = chromadb.PersistentClient(path=str(DB_FOLDER))
    collection = client.get_collection(
        name="pedoman_pi",
        embedding_function=BGEM3EF(model_path=MODEL_PATH), # type: ignore[arg-type]
    )
    results = collection.query(query_texts=[question], n_results=n_results)
    documents = results.get("documents") or [[]]
    chunks = documents[0] if documents and documents[0] else []
    return "\n\n".join(chunk for chunk in chunks if chunk)


def main() -> None:
    question = input("Apa yang ingin Anda tanyakan? ").strip()
    if not question:
        print("Pertanyaan tidak boleh kosong.")
        return

    context = retrieve_context(question)
    print(f"\n=== KONTEKS HASIL RETRIEVAL ===\n{context}")


if __name__ == "__main__":
    main()