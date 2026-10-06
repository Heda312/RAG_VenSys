import chromadb

client = chromadb.PersistentClient(path="D:\\RAG_Project\\storages\\chroma_db")
collection = client.get_collection(name="pedoman_pi")
get_data = collection.get()

print(f"Data yang diambil dari DB: {get_data}")