from sentence_transformers import SentenceTransformer

# 1. Cek semua method & atribut yang ada di class
print(dir(SentenceTransformer))

# 2. Cek docstring lengkap method encode
help(SentenceTransformer.encode)