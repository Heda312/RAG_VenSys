import requests

payload = {
    "model": "hf.co/Qwen/Qwen3-VL-4B-Instruct-GGUF:latest",
    "prompt": "Jelaskan RAG dalam 2 paragraf",
    "stream": False,
}

response = requests.post("http://localhost:11434/api/generate", json=payload).json()

# Ambil data dari JSON
eval_count = response["eval_count"]  # Jumlah token jawaban
eval_duration_ns = response["eval_duration"]  # Waktu dalam nanosecond

# Hitung token/second (1 detik = 1.000.000.000 nanosecond)
tokens_per_second = eval_count / (eval_duration_ns / 1e9)
tokens_per_minute = tokens_per_second * 60

print(f"Hasil Jawaban Token: {eval_count}")
print(f"Kecepatan: {tokens_per_second:.2f} token/detik")
print(f"Kecepatan: {tokens_per_minute:.2f} token/menit")