# Pengujian kualitas chunking

Pengujian lokal tanpa LangChain atau inference model. Hitungan token menggunakan
package `tokenizers` dan file tokenizer resmi BGE-M3; keduanya diperlukan setelah
penambahan strategi token. Setelah persiapan, seluruh evaluasi berjalan offline.
Ada dua lapisan: unit test untuk memeriksa perhitungan evaluator dan quality gate
yang membaca empat artefak JSON aktual. Laporan memberikan metrik dan nomor chunk
yang perlu ditinjau; tidak menghasilkan klaim akurasi RAG atau skor pemenang buatan.

## Menjalankan

Dari root project pada PowerShell:

```powershell
Set-Location 'D:\RAG VenSys'

# Buat/perbarui hasil chunk berbasis token dari TXT bersih.
.\.venv\Scripts\python.exe .\src\Stages\1_pdf_loader\chunking_token.py

# Buat laporan empat strategi: Markdown, JSON, dan HTML.
.\.venv\Scripts\python.exe .\src\Stages\1_pdf_loader\testing\evaluate_chunking.py

# Jalankan unit test evaluator dan quality gate data aktual.
.\.venv\Scripts\python.exe -m unittest discover -s .\src\Stages\1_pdf_loader\testing -p 'test_*.py' -v
```

Alternatif VS Code: pilih interpreter `.venv`, buka `evaluate_chunking.py` lalu
**Run Python File** untuk laporan. `test_chunking_quality.py` menjalankan pengujian
evaluator/data; `test_token_chunking.py` menjalankan pengujian token. Gunakan unittest
discover di atas untuk keduanya. Path dihitung dari lokasi script.

Untuk menjalankan hanya unit test alat ukur:

```powershell
Set-Location 'D:\RAG VenSys\src\Stages\1_pdf_loader\testing'
& '..\..\..\..\.venv\Scripts\python.exe' -m unittest test_chunking_quality.TestQualityMetrics -v
```

Laporan ada di `testing/reports/chunking_quality.md`, `chunking_quality.json`, dan
**`chunking_quality.html`**. Buka file HTML dengan browser untuk melihat dashboard
offline; tidak memerlukan server, koneksi internet, atau CDN.
Menjalankan evaluator lagi mengganti ketiga laporan tersebut. File sumber, empat JSON
chunk, dan script pembuat chunk tidak diubah. Exit 0 evaluator berarti laporan
berhasil dibuat; status lulus/gagal gate diperoleh dari exit code `unittest`.

## Visualisasi

Dashboard menampilkan ringkasan empat strategi, tabel coverage dan rekonstruksi,
grafik panjang setiap chunk, distribusi panjang pada skala persentase yang sama,
temuan overlap, dan tabel metadata per chunk.

Gunakan pilihan **Strategi** untuk berpindah antara empat JSON. Pilihan **Ukuran yang
dilihat** menyediakan seluruh chunk dalam kata, isi inti dalam kata, serta seluruh
chunk dalam token BGE-M3. Grafik panjang dan tabel detail mengikuti strategi terpilih.
Grafik distribusi membandingkan keempat strategi memakai satuan pilihan yang sama.
Rentang 96–480 token adalah acuan pembanding konfigurasi awal, bukan batas input model
atau ukuran ideal universal. Tooltip batang menampilkan nilai sesuai satuan.
Isi tabel tetap tersedia sebagai alternatif aksesibel terhadap grafik.

Jika hanya ingin memperbarui HTML, jalankan `visualize_chunking.py` melalui Run Python
File. Script tersebut melakukan audit ulang dan membuat HTML; laporan MD/JSON lama
baru diperbarui saat `evaluate_chunking.py` dijalankan.

`chunking_dashboard.html` adalah template untuk generator, bukan laporan yang dibuka
langsung. Data snapshot disisipkan oleh `render_dashboard()` dengan escaping teks.

## File yang dibandingkan

| Artefak | Sumber pembanding | Isi chunk |
| --- | --- | --- |
| `Pedoman PI_chunks_char.json` | `Pedoman PI_cleaned.txt` | `text` |
| `Pedoman PI_chunks_header.json` | `Pedoman PI.md` | `content` |
| `Pedoman PI_chunks_header_overlapping.json` | `Pedoman PI.md` | `content`, dengan wrapper overlap dipisahkan |
| `Pedoman PI_chunks_token.json` | `Pedoman PI_cleaned.txt` | `text`, budget token dan offset kata |

Nama `char` tidak berarti panjangnya diukur dalam karakter: script saat ini memakai
kata. Jangan menyamakan 480 kata dengan 480 token model.

## Strategi token BGE-M3

`chunking_token.py` memakai budget **480 token isi** dan overlap **maksimum 96 token**.
Kandidat potongan dihitung ulang memakai tokenizer asli. Pemotongan dilakukan pada
batas kata agar tidak merusak teks/subword/Unicode; jumlah token dapat lebih kecil dari
budget. Overlap dapat berkurang untuk memberi ruang bagi kata baru. Satu kata yang
sendiri melebihi budget menghasilkan error jelas, bukan truncation tersembunyi.

Daftar isi dan isi utama dipisahkan dengan aturan dokumen contoh `1. PENDAHULUAN`,
sama seperti baseline word chunk. Aturan ini belum universal untuk semua PDF.
Whitespace dinormalisasi menjadi spasi. Metadata menyimpan `token_count` tanpa special
tokens, `input_token_count` dengan special tokens, budget, overlap aktual, model/revision/
SHA-256 tokenizer, serta `word_start`/`word_end` global (berbasis 0, end eksklusif).

Evaluator menghitung ulang token semua strategi menggunakan tokenizer yang sama.
Untuk varian token, offset diperiksa terhadap kata sumber sebelum rekonstruksi;
tidak mengandalkan tebakan overlap terpanjang. Pemeriksaan model memakai batas 8192
termasuk special tokens. Angka ini tidak mengukur tokenizer Qwen atau reranker, dan
belum menjadi pengujian kesetaraan tokenisasi terhadap runtime Ollama.

Tokenizer bersumber dari [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3), revision
`5617a9f61b028005a4858fdac845db406aefb181`. Pengaturan special tokens mengikuti
[API tokenizer Hugging Face](https://huggingface.co/docs/transformers/main_classes/tokenizer).
File sekitar 17 MB disimpan di `.cache/bge-m3/tokenizer.json` dan dikecualikan dari Git.
Bobot embedding/LLM tidak diperlukan. Package `tokenizers` ditulis eksplisit di requirements.

Pada komputer baru, lakukan persiapan sekali dari root project (memerlukan internet):

```powershell
.\.venv\Scripts\python.exe -m pip install tokenizers
New-Item -ItemType Directory -Force -Path '.cache\bge-m3' | Out-Null
Invoke-WebRequest -Uri 'https://huggingface.co/BAAI/bge-m3/resolve/5617a9f61b028005a4858fdac845db406aefb181/tokenizer.json' -OutFile '.cache\bge-m3\tokenizer.json' -UseBasicParsing
```

Untuk server offline, salin file tokenizer ke path yang sama. Evaluator tidak
mengunduh otomatis dan akan memberi pesan jelas bila cache belum tersedia.

## Metrik dan interpretasi

- **JSON standar:** file harus bisa dibaca `json.loads`. Baris `_comment ...` di luar
  struktur JSON membuat gate gagal. Evaluator hanya menoleransi satu baris pembuka
  tersebut untuk melanjutkan diagnosis; status JSON tetap gagal. Sintaks rusak lain
  menghasilkan error baca yang dilaporkan per file.
  Parser juga menolak key duplikat serta `NaN`/`Infinity`, yang diterima oleh parser
  Python default tetapi tidak layak dianggap JSON standar yang valid untuk audit ini.
- **Schema:** isi tidak kosong, word count dan indeks sesuai, serta metadata heading
  konsisten. Schema yang benar belum menjamin metadata lengkap untuk RAG.
- **Ukuran:** kata minimum, median, rata-rata, maksimum, dan nomor chunk di luar
  rentang 50–600 kata. Ini peringatan tinjauan, bukan gate mutlak: bagian pendek atau
  tabel panjang bisa sah. Batas tersebut bukan batas context model.
- **Token:** min/median/rata-rata/max token BGE-M3 pada semua strategi, hitungan per
  chunk dengan/tanpa special tokens, dan daftar chunk yang melebihi batas model.
- **Coverage:** proporsi window 5 kata bersebelahan dari sumber yang ditemukan di
  setidaknya satu chunk. Whitespace dinormalisasi; urutan kata, huruf, dan tanda baca
  dipertahankan. Nilai 95% hanya acuan tinjauan yang bisa diubah melalui konstanta,
  bukan gate kehilangan isi.
- **Coverage body heading:** baris heading dikeluarkan dari sumber karena disimpan
  dalam metadata. Coverage sumber penuh juga dilaporkan, tanpa menghitung metadata
  sebagai isi chunk. Window yang melintasi batas bagian bisa hilang meski tidak ada
  kata yang hilang. Metrik bukan pembuktian rekonstruksi sempurna.
- **Rekonstruksi isi:** quality gate kelengkapan kini membandingkan urutan kata penuh
  hasil rekonstruksi dengan sumber. Versi heading menggabungkan isi inti. Versi word
  chunk menghapus overlap suffix–prefix terpanjang antar-chunk dalam section sama.
  Pengulangan pada batas section berbeda tetap dipertahankan. Ini asumsi khusus format
  chunk saat ini: pengulangan alami antar-chunk dalam section sama dapat ambigu tanpa
  metadata offset. Hasil mencatat jumlah kata dan lokasi perbedaan pertama bila gagal.
- **Duplikasi:** mendeteksi chunk identik setelah normalisasi whitespace. Pengulangan
  sah dalam dokumen tetap perlu ditinjau jika gate ini gagal.
- **Overlap:** jumlah kata prefix/suffix bersebelahan dan jumlah kata wrapper tambahan.
  Versi heading diperiksa agar wrapper hanya membawa suffix isi inti sebelumnya,
  bukan akumulasi overlap lama. Overlap lintas section dicatat untuk tinjauan topik.
  Pencocokan menggunakan kata utuh sehingga suffix sebagian kata tidak lolos.
  Chunk pertama tidak boleh membawa prefix overlap dari chunk sebelumnya.
- **Konsistensi varian heading:** jumlah chunk, metadata, dan isi inti harus identik
  sebelum/sesudah penambahan overlap. Ini memungkinkan perbandingan yang lebih adil.
  File heading tanpa overlap menjadi referensi batas isi inti, agar penutup `]` yang
  ikut tersalin pada overlap tidak salah dianggap sebagai akhir wrapper terluar.
- **Sumber/halaman:** nama sumber harus string tidak kosong; halaman harus integer
  positif (berbasis 1). Boolean, angka negatif, dan string tidak dianggap halaman
  valid. Lokasi tersebut tetap belum diverifikasi terhadap PDF asli.

## Perbaikan unit test

Kasus regresi mencakup coverage yang turun di batas chunk walaupun isi lengkap,
hilangnya bagian berulang, urutan tertukar, kata tambahan, pemisahan section,
overlap sebagian kata, metadata boolean yang sebelumnya dianggap angka, input kosong,
nama strategi tidak valid, JSON nonstandar, isolasi satu file yang gagal dibaca,
dan escaping data HTML. Pengujian artefak tetap melaporkan cacat data sebagai gagal;
assertion tidak dilonggarkan supaya semua hasil terlihat hijau.

Selain 26 test evaluator, tersedia 9 test token/integrasi: subword asli, Unicode,
budget, overlap nol/tinggi, kemajuan offset, input kosong, kata terlalu panjang,
metadata rusak, rekonstruksi, dan perhitungan token pada keempat artefak.
Snapshot pembaruan ini menghasilkan 27 chunk token. Masih ada 1 test artefak gagal
pada propagasi overlap heading di chunk
`6, 16, 17, 19, 20, 26, 29, 30, 41, 47, 59`. JSON keempat input sudah valid pada
snapshot ini dan rekonstruksi kata semuanya identik. Jalankan ulang untuk status terbaru.

Coverage memakai kecocokan window, sehingga frasa berulang dapat cocok di lokasi lain.
Kata tambahan/redundansi juga tidak otomatis membuat coverage turun. Rasio jumlah kata
chunk/sumber disediakan sebagai konteks, bukan skor redundansi murni atau akurasi.

## Batas kesimpulan

Sumber TXT bersih dan Markdown berbeda; angka coverage tidak boleh langsung dipakai
untuk menetapkan strategi terbaik. Belum ada pengecekan semantik, integritas baris
tabel, akurasi OCR, ataupun kualitas jawaban LLM. Ukuran token BGE-M3 sudah diukur.

Untuk memilih chunking bagi RAG, lanjutkan dengan pertanyaan nyata dan lokasi jawaban
acuan, lalu ukur Recall@k, peringkat setelah reranking, dan ketepatan kutipan. Gunakan
model, konfigurasi retrieval, serta dokumen yang sama untuk setiap strategi.

## Fungsi utama

| Fungsi | Tanggung jawab |
| --- | --- |
| `load_records` | Membaca JSON dan menyimpan error sintaks standar |
| `split_overlap` | Memisahkan prefix overlap dari isi inti |
| `source_coverage` | Menghitung coverage window kata beserta contoh yang hilang |
| `adjacent_overlap` | Mencari kesamaan suffix–prefix antar-chunk |
| `reconstruct_source` | Memeriksa kesamaan urutan kata penuh dengan sumber |
| `analyze_records` | Mengecek schema dan menghitung metrik setiap strategi |
| `compare_header_versions` | Mendeteksi perubahan isi/metadata selain overlap |
| `evaluate_all` | Mengumpulkan hasil empat file secara independen |
| `chunk_by_tokens` | Membentuk potongan berbatas token dengan kata utuh |
| `audit_token_offsets` | Memeriksa offset, budget, identitas tokenizer, dan rekonstruksi token chunk |
| `measure_tokens` | Menghitung token semua strategi dengan tokenizer sama |
| `markdown_report` / `main` | Membuat laporan yang bisa dibaca dan dianalisis ulang |
| `render_dashboard` | Menyisipkan hasil audit pada template HTML mandiri |
