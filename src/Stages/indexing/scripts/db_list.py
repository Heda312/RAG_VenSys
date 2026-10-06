import chromadb

client = chromadb.PersistentClient(path="D:\\RAG_Project\\storages\\chroma_db")
collection = client.get_collection(name="pedoman_pi")

print("Collection yang tersedia:", client.list_collections())