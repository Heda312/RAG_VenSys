# RAG Project

Proyek eksperimen **Retrieval-Augmented Generation (RAG)** untuk menjawab pertanyaan berdasarkan dokumen PDF. Pipeline yang tersedia mencakup ekstraksi teks, cleaning, chunking, embedding BGE-M3, penyimpanan dan pencarian dengan ChromaDB, lalu generation dengan model lokal melalui Ollama.

> Repository ini masih berupa kumpulan script tahap per tahap. Belum ada aplikasi web/API yang menyatukan seluruh pipeline. Beberapa path antar-script perlu diselaraskan sebelum pipeline dokumen bisa dijalankan dari awal sampai akhir.

## Alur sistem

```text
PDF
  -> ekstraksi teks (PyMuPDF4LLM, OCR dimatikan)
  -> cleaning dan chunking
  -> embedding BGE-M3
  -> ChromaDB (koleksi pedoman_pi)
  -> retrieval top-k (Tahap pengembangan akan ditambahkan model reranking)
  -> Ollama chat dengan konteks hasil retrieval
```

Embedding untuk dokumen dan pertanyaan menggunakan `BAAI/bge-m3` melalui `SentenceTransformer` di `src/embedding_utils.py`. Generator mengirim konteks retrieval ke Ollama melalui API lokal `http://localhost:11434/api/chat`. Riwayat percakapan belum disimpan atau dikirim ke model; setiap pertanyaan diproses sebagai permintaan baru.

## Struktur utama

```text
src/embedding_utils.py
src/Stages/pdf_loader/extractor.py
src/Stages/pdf_loader/cleaner_data.py
src/Stages/pdf_loader/chunker.py
src/Stages/indexing/embedding_test.py
src/Stages/indexing/db_indexing.py
src/Stages/retrieval/querying.py
src/Stages/generation/scripts/llm_generator.py
src/Stages/generation/scripts/modelfile
storages/inputs/       # PDF sumber
storages/outputs/      # Hasil tahap pemrosesan
storages/chroma_db/    # Penyimpanan persisten ChromaDB
```

## Persiapan

1. Gunakan Python yang sesuai dengan environment proyek dan pasang dependency:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. Pastikan Ollama sudah terpasang dan berjalan. Generator saat ini memakai model `qwen3:4b-rag`; periksa nama yang tersedia dengan:

   ```powershell
   ollama list
   ```

   Jika model itu belum tersedia tetapi Modelfile ingin digunakan, buat modelnya dengan nama tersebut:

   ```powershell
   ollama create qwen3:4b-rag -f src/Stages/generation/scripts/modelfile
   ```

3. Letakkan PDF yang akan diproses di `storages/inputs/`. `extractor.py` saat ini menunjuk ke `storages/inputs/Pedoman PI.pdf`.

## Menjalankan generator

Untuk bertanya pada dokumen yang sudah terindeks:

```powershell
.\.venv\Scripts\python.exe src/Stages/generation/scripts/llm_generator.py
```

Generator meminta pertanyaan berulang kali. Ketik `keluar` atau tekan Enter kosong untuk mengakhiri sesi. Untuk melihat konteks retrieval saja:

```powershell
.\.venv\Scripts\python.exe src/Stages/retrieval/querying.py
```

Generator mengambil lima hasil retrieval secara default dari koleksi `pedoman_pi`, lalu mengirimkannya bersama pertanyaan ke Ollama. Jika informasi tidak ditemukan di konteks, prompt mengarahkan model agar tidak mengarang. Kualitas jawaban tetap bergantung pada isi dan relevansi chunk yang ditemukan.

## Pipeline indexing: periksa path sebelum menjalankan

Script ekstraksi, cleaning, chunking, embedding, dan indexing belum memakai satu rangkaian path yang konsisten. Path yang sekarang ditetapkan di kode:

| Tahap | Input | Output |
| --- | --- | --- |
| Ekstraksi | `storages/inputs/Pedoman PI.pdf` | `storages/outputs/extraction/Pedoman PI.txt` |
| Cleaning | `storages/outputs/extraction/Pedoman PI_1.txt` | `storages/outputs/extraction/Pedoman PI_1_cleaned.txt` |
| Chunking | `storages/outputs/extraction/Pedoman PI_cleaned.txt` | `storages/outputs/extraction/Pedoman PI_chunks.json` |
| Embedding | `storages/outputs/text_chunked/Pedoman PI_chunks.json` | `storages/outputs/vector_embed/Pedoman PI_embedded000.json` |
| Indexing | `storages/outputs/vector_embed/Pedoman PI_embedded.json` | ChromaDB `pedoman_pi` |

Nama/path yang tidak cocok membuat tahap berikutnya gagal menemukan input. Selaraskan path tersebut sebelum menjalankan pipeline dari PDF. Jangan mengindeks ulang dengan embedding model berbeda ke koleksi yang sama; query dan dokumen harus berada dalam ruang embedding yang sama.

## Konfigurasi penting

- Database ChromaDB: `storages/chroma_db`
- Nama koleksi: `pedoman_pi`
- Embedding: `BAAI/bge-m3` melalui Sentence Transformers
- Jumlah hasil retrieval default: `n_results=5` di `src/Stages/retrieval/querying.py`
- Model generation: `qwen3:4b-rag` di `src/Stages/generation/scripts/llm_generator.py`
- Ollama chat API: `http://localhost:11434/api/chat`
- OCR: dimatikan pada extractor (`use_ocr=False`); PDF scan mungkin tidak menghasilkan teks yang bisa dicari

## Batasan saat ini

- Belum ada memory percakapan, penyimpanan chat, UI, atau API backend.
- Retrieval mengembalikan teks chunk tanpa metadata sumber yang ditampilkan bersama jawaban.
- `cleaner_data.py`, `chunker.py`, `embedding_test.py`, dan `db_indexing.py` memiliki path yang perlu diselaraskan seperti tabel di atas.
- `requirements.txt` memuat paket untuk beberapa eksperimen/proposal; belum semua dependency dipakai oleh alur generator.
- Belum ada klaim evaluasi akurasi atau pengujian end-to-end seluruh pipeline dalam README ini.