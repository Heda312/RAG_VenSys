from pathlib import Path
import json
import sys

import requests

PROJECT_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if parent.name == "RAG_Project"
)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.Stages.retrieval.querying import retrieve_context


MODEL = "qwen3:4b-rag"
OLLAMA_URL = "http://localhost:11434/api/chat"
NOT_FOUND = "Maaf, informasi tersebut tidak ditemukan dalam dokumen pedoman."

SYSTEM_PROMPT = f'''
Kamu adalah asisten AI yang jujur, presisi, dan terikat penuh pada dokumen yang diberikan.

TUGAS UTAMA:
Jawablah pertanyaan pengguna HANYA berdasarkan konteks dokumen RAG yang dilampirkan.

ATURAN STRICT (ANTI-HALUSINASI):
1. DILARANG MENGGUNAKAN pengetahuan di luar konteks yang diberikan.
2. DILARANG mengarang, berasumsi, atau melengkapi jawaban dengan informasi eksternal.
3. Jika data yang ada ternyata kurang berikan koreksi dan berikan alasannya.
4. Berikan jawaban yang ringkas, jelas, dan langsung pada intinya.
'''

def stream_answer(question: str):
    context = retrieve_context(question)
    if not context or not context.strip():
        yield NOT_FOUND
        return

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Konteks dokumen:\n{context}\n\nPertanyaan: {question}",
            },
        ],
        "stream": True,
    }

    with requests.post(
        OLLAMA_URL, json=payload, stream=True, timeout=(10, None)
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            text = chunk.get("message", {}).get("content", "")
            if text:
                yield text


def main() -> None:
    print("Tanya dokumen. Ketik 'keluar' atau tekan Enter kosong untuk berhenti.")
    while True:
        question = input("\nPertanyaan: ").strip()
        if not question or question.lower() == "keluar":
            print("Sesi selesai.")
            break

        print("\nJawaban:")
        for text in stream_answer(question):
            print(text, end="", flush=True)
        print()


if __name__ == "__main__":
    main()
