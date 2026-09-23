# Hasil audit kualitas chunking

Audit statis terhadap sumber ekstraksi masing-masing, bukan PDF asli atau kualitas retrieval.
Ukuran kata dan token BGE-M3 diukur terpisah. Tidak ada skor gabungan/pemenang otomatis.

| Strategi | Chunk | Kata min/median/max | Pendek | Panjang | Coverage body 5-kata | JSON standar |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| char | 17 | 127/480/480 | 0 | 0 | 99.94% | LULUS |
| header | 63 | 1/76/821 | 27 | 1 | 95.91% | LULUS |
| header_overlap | 63 | 19/107/845 | 17 | 1 | 95.91% | LULUS |
| token | 27 | 118/292/335 | 0 | 0 | 99.94% | LULUS |

## char

Sumber: `Pedoman PI_cleaned.txt`.

- JSON ketat: valid.
- Token BGE-M3 min/median/max: 368/762/878 (tanpa special tokens).
- Chunk melewati 8192 token termasuk special tokens: [].
- Error schema: 0; [].
- Chunk pendek (< 50 kata): [].
- Chunk panjang (> 600 kata): [].
- Chunk duplikat persis setelah normalisasi whitespace: [].
- Chunk tanpa nama sumber: [].
- Chunk tanpa halaman: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17].
- Rasio jumlah kata inti / kata sumber body: 1.231 (bukan skor).
- Total kata prefix overlap: 0.
- Rekonstruksi urutan kata sumber: IDENTIK (6240/6240 kata).
- Coverage sumber penuh termasuk heading: 99.94%.
- Contoh window body tidak ditemukan: ['. 32 | 2 1.', '32 | 2 1. PENDAHULUAN', '| 2 1. PENDAHULUAN 1.1.', '2 1. PENDAHULUAN 1.1. Latar'].
- Overlap bersebelahan (kata) min/median/max: 96/96/96.

## header

Sumber: `Pedoman PI.md`.

- JSON ketat: valid.
- Token BGE-M3 min/median/max: 1/120/1397 (tanpa special tokens).
- Chunk melewati 8192 token termasuk special tokens: [].
- Error schema: 0; [].
- Chunk pendek (< 50 kata): [5, 6, 15, 16, 18, 19, 21, 25, 27, 28, 29, 35, 36, 40, 44, 46, 52, 53, 54, 55, 56, 58, 59, 60, 61, 62, 63].
- Chunk panjang (> 600 kata): [4].
- Chunk duplikat persis setelah normalisasi whitespace: [].
- Chunk tanpa nama sumber: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63].
- Chunk tanpa halaman: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63].
- Rasio jumlah kata inti / kata sumber body: 1.000 (bukan skor).
- Total kata prefix overlap: 0.
- Rekonstruksi urutan kata sumber: IDENTIK (5988/5988 kata).
- Coverage sumber penuh termasuk heading: 90.23%.
- Contoh window body tidak ditemukan: ['Pustaka ……………………………………………. 32| 2 Mata', '……………………………………………. 32| 2 Mata kuliah', '32| 2 Mata kuliah Penulisan', '2 Mata kuliah Penulisan Ilmiah', 'mahasiswa dalam proses pengerjaannya. Tujuan'].

## header_overlap

Sumber: `Pedoman PI.md`.

- JSON ketat: valid.
- Token BGE-M3 min/median/max: 46/172/1429 (tanpa special tokens).
- Chunk melewati 8192 token termasuk special tokens: [].
- Error schema: 0; [].
- Chunk pendek (< 50 kata): [5, 15, 16, 18, 19, 25, 28, 40, 52, 53, 54, 55, 58, 59, 60, 62, 63].
- Chunk panjang (> 600 kata): [4].
- Chunk duplikat persis setelah normalisasi whitespace: [].
- Chunk tanpa nama sumber: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63].
- Chunk tanpa halaman: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63].
- Rasio jumlah kata inti / kata sumber body: 1.000 (bukan skor).
- Total kata prefix overlap: 1552.
- Rekonstruksi urutan kata sumber: IDENTIK (5988/5988 kata).
- Coverage sumber penuh termasuk heading: 90.23%.
- Contoh window body tidak ditemukan: ['Pustaka ……………………………………………. 32| 2 Mata', '……………………………………………. 32| 2 Mata kuliah', '32| 2 Mata kuliah Penulisan', '2 Mata kuliah Penulisan Ilmiah', 'mahasiswa dalam proses pengerjaannya. Tujuan'].
- Overlap bersebelahan (kata) min/median/max: 2/26/37.
- Prefix bukan suffix isi inti sebelumnya: [6, 16, 17, 19, 20, 26, 29, 30, 41, 47, 59].
- Overlap antar-section: 62 pasangan (perlu tinjauan konteks).

## token

Sumber: `Pedoman PI_cleaned.txt`.

- JSON ketat: valid.
- Token BGE-M3 min/median/max: 217/480/480 (tanpa special tokens).
- Chunk melewati 8192 token termasuk special tokens: [].
- Error schema: 0; [].
- Chunk pendek (< 50 kata): [].
- Chunk panjang (> 600 kata): [].
- Chunk duplikat persis setelah normalisasi whitespace: [].
- Chunk tanpa nama sumber: [].
- Chunk tanpa halaman: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27].
- Rasio jumlah kata inti / kata sumber body: 1.236 (bukan skor).
- Total kata prefix overlap: 0.
- Rekonstruksi urutan kata sumber: IDENTIK (6240/6240 kata).
- Coverage sumber penuh termasuk heading: 99.94%.
- Contoh window body tidak ditemukan: ['. 32 | 2 1.', '32 | 2 1. PENDAHULUAN', '| 2 1. PENDAHULUAN 1.1.', '2 1. PENDAHULUAN 1.1. Latar'].
- Overlap bersebelahan (kata) min/median/max: 39/59/70.

## Konsistensi versi heading

Isi inti dan metadata identik pada kedua versi.

## Cara membaca

Coverage menguji window kata sumber yang muncul utuh di suatu chunk. Whitespace dinormalisasi; huruf dan tanda baca dipertahankan. Window berulang dapat cocok pada lokasi lain. Batas chunk tanpa overlap dapat mengurangi coverage walaupun semua kata tersimpan.

Untuk heading, coverage body mengabaikan baris heading sumber dan wrapper overlap. Coverage penuh tidak memasukkan metadata heading sehingga lebih rendah belum tentu kehilangan isi. Sumber TXT bersih dan Markdown berbeda; persentase antar-strategi tidak menentukan pemenang langsung.

Batas 50–600 kata adalah penanda tinjauan; chunk pendek bisa valid. Coverage di bawah 95% adalah penanda tinjauan, bukan kegagalan kehilangan isi. Gate kelengkapan memakai rekonstruksi urutan kata; pada word chunk diasumsikan overlap suffix-prefix terpanjang dalam section sama. Kecocokan makna, integritas tabel, nomor halaman asli, dan jawaban RAG tetap perlu evaluasi terpisah.

Untuk memilih strategi, gunakan pertanyaan berjawaban acuan dan sumber benar, lalu bandingkan Recall@k, peringkat setelah reranking, dan ketepatan kutipan memakai model/config yang sama.
