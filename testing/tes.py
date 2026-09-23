import requests  # Import library requests buat komunikasi sama API


# ==========================================
# 1. CONTOH GET REQUEST (Ambil Data)
# ==========================================

# URL endpoint yang mau kita tembak
url_get = "https://jsonplaceholder.typicode.com/posts/1"

# Mengirim request GET ke server
response_get = requests.get(url_get)

# Mengecek status code (200 artinya sukses)
print(f"Status Code GET: {response_get.status_code}")

# `.json()` berguna buat ngubah respon string/text dari server jadi dictionary Python
data_get = response_get.json()

# Nampilin isi data dictionary
print(f"Hasil GET Data: {data_get}")
print(f"User ID    : {data_get['userId']}")
print(f"Id         : {data_get['id']}")
print(f"Judul Post : {data_get['title']}")
print(f"Isi Body   : {data_get['body']}\n")


# ==========================================
# 2. CONTOH POST REQUEST (Kirim Data)
# ==========================================

# URL endpoint buat nambah data
url_post = "https://jsonplaceholder.typicode.com/posts"

# Data berbentuk dictionary Python yang mau kita kirim ke server
payload_data = {
    "userId": 1,

    "title": "Script Python ciptaan Way",
    "body": "Narik API pake Python ternyata simpel banget!",
}

# Mengirim request POST.
# Parameter `json=payload_data` otomatis ngubah dictionary Python jadi format JSON
# sekaligus nge-set Header 'Content-Type': 'application/json' secara otomatis.
response_post = requests.post(url_post, json=payload_data)
        
# Mengecek status code (201 artinya data berhasil dibuat/dikirim)
print(f"Status Code POST: {response_post.status_code}")

# Mengambil respon balik dari server (simulasi data tersimpan)
data_post = response_post.json()

print("Hasil Respon POST dari Server:")
print(data_post)