# File: src/embedding_utils.py
from pathlib import Path
import chromadb
from chromadb.api.types import Documents, Embeddings
from sentence_transformers import SentenceTransformer

current_file = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in current_file.parents if p.name == "RAG_Project")
# Use the same Hugging Face model ID used for the cached local model.
# `D:/models/bge-m3:latest` is an Ollama-style tag, not a SentenceTransformers path.
MODEL_PATH = "BAAI/bge-m3"

class BGEM3EF(chromadb.EmbeddingFunction[Documents]):

  def __init__(self, model_path: Path | str = MODEL_PATH):
    self.model = SentenceTransformer(str(model_path), device="cpu")

  def name(self) -> str:
    return "bge-m3"

  def __call__(self, input: Documents) -> Embeddings:
    embeddings = self.model.encode(input, convert_to_numpy=True)
    return embeddings.tolist()

  def embed_query(self, input: Documents) -> Embeddings:
    return self.__call__(input)
