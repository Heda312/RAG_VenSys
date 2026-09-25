from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3")

sentences = [
    "That is a happy person",
]
embeddings = model.encode(sentences)

similarities = model.similarity(embeddings, embeddings)

print(similarities)