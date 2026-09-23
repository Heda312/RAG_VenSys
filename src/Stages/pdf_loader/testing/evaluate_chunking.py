"""Audit empat artefak chunk lokal dalam kata dan token BGE-M3."""

import json
import re
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median


LOADER_DIR = Path(__file__).resolve().parents[1]
# Folder stage bukan package Python; pakai lokasi file, bukan working directory.
if str(LOADER_DIR) not in sys.path:
    sys.path.insert(0, str(LOADER_DIR))
from chunking_token import (
    count_tokens, load_tokenizer, tokenizer_identity, MODEL_INPUT_LIMIT,
    CHUNK_TOKENS, OVERLAP_TOKENS,
)
OUTPUT_DIR = LOADER_DIR / "output"
REPORT_DIR = Path(__file__).resolve().parent / "reports"
CASES = {
    "char": ("Pedoman PI_chunks_char.json", "Pedoman PI_cleaned.txt"),
    "header": ("Pedoman PI_chunks_header.json", "Pedoman PI.md"),
    "header_overlap": ("Pedoman PI_chunks_header_overlapping.json", "Pedoman PI.md"),
    "token": ("Pedoman PI_chunks_token.json", "Pedoman PI_cleaned.txt"),
}
# Batas kata adalah heuristik audit yang bisa diubah, bukan batas token BGE-M3.
MIN_WORDS = 50
MAX_WORDS = 600
WINDOW_WORDS = 5
MIN_SOURCE_WINDOW_COVERAGE = 0.95
HEADER_LINE = re.compile(r"(?m)^#{1,6}[ \t]+.*$")
OVERLAP_PREFIX = re.compile(r"^\[\.\.\. (.*?)\]\r?\n\r?\n", re.DOTALL)


def strict_json(raw):
    """Refuse non-standard NaN/Infinity and duplicate keys hidden by json.loads."""
    def reject_constant(value):
        raise ValueError(f"Konstanta JSON tidak standar: {value}")

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Key JSON duplikat: {key}")
            result[key] = value
        return result

    return json.loads(raw, parse_constant=reject_constant, object_pairs_hook=unique_object)


def load_records(path):
    """Validasi JSON ketat; hanya toleransi satu baris _comment untuk diagnosis."""
    raw = path.read_text(encoding="utf-8-sig")
    strict_error = None
    try:
        records = strict_json(raw)
    except json.JSONDecodeError as error:
        strict_error = f"Baris {error.lineno}, kolom {error.colno}: {error.msg}"
        # Toleransi ini tidak mengubah status gagal JSON atau menulis ulang input.
        lines = raw.splitlines(keepends=True)
        if not lines or not lines[0].startswith("_comment "):
            raise ValueError(f"JSON rusak: {strict_error}") from error
        records = strict_json("".join(lines[1:]))
    if not isinstance(records, list) or not records:
        raise ValueError("Root harus berupa list chunk yang tidak kosong.")
    return records, strict_error


def split_overlap(text, expected_core=None):
    """Pisahkan wrapper; referensi inti mengatasi penutup ] yang ikut tersalin.

    Bila isi inti berubah, fallback dipakai agar perbandingan tetap melaporkannya.
    """
    if expected_core and text.startswith("[... "):
        for separator in ("]\n\n", "]\r\n\r\n"):
            suffix = separator + expected_core
            if text.endswith(suffix):
                return text[5:-len(suffix)], expected_core
    match = OVERLAP_PREFIX.match(text)
    return (match.group(1), text[match.end():]) if match else ("", text)


def windows(words, width=WINDOW_WORDS):
    """Buat urutan kata bersebelahan; teks pendek memakai satu window utuh."""
    if type(width) is not int or width < 1:
        raise ValueError("Lebar window harus integer positif.")
    if not words:
        return []
    width = min(width, len(words))
    return [tuple(words[i:i + width]) for i in range(len(words) - width + 1)]


def source_coverage(source, texts):
    """Ukur proporsi window sumber yang muncul utuh di setidaknya satu chunk.

    Tidak menyambung antar-chunk: kehilangan konteks pada batas ikut terdeteksi.
    Window berulang dinilai menurut posisi sumber tetapi kecocokannya berdasarkan
    isi. Metrik ini bukan jaminan rekonstruksi, urutan, atau kelengkapan semantik.
    """
    source_words = source.split()
    if not source_words:
        raise ValueError("Teks sumber kosong; coverage tidak dapat dihitung.")
    width = min(WINDOW_WORDS, len(source_words))
    source_windows = windows(source_words, width)
    chunk_windows = {
        item for text in texts if len(text.split()) >= width
        for item in windows(text.split(), width)
    }
    missing = [item for item in source_windows if item not in chunk_windows]
    return {
        "ratio": 1 - len(missing) / len(source_windows),
        "source_windows": len(source_windows),
        "missing_windows": len(missing),
        "missing_examples": list(dict.fromkeys(" ".join(x) for x in missing))[:5],
    }


def adjacent_overlap(left, right):
    """Hitung kecocokan kata suffix chunk kiri dengan prefix chunk kanan."""
    left_words, right_words = left.split(), right.split()
    for size in range(min(len(left_words), len(right_words)), 0, -1):
        if left_words[-size:] == right_words[:size]:
            return size
    return 0


def reconstruct_source(source, cores, sections, strategy):
    """Bandingkan urutan kata penuh, termasuk kemunculan berulang dan kata ekstra.

    Heading: gabungkan inti. Word chunk: buang suffix-prefix terpanjang hanya di
    section sama. Asumsi overlap ini dilaporkan; bukan bukti terhadap PDF asli.
    """
    rebuilt = []
    for i, core in enumerate(cores):
        overlap = (adjacent_overlap(cores[i - 1], core)
                   if strategy == "char" and i and sections[i - 1] == sections[i] else 0)
        rebuilt.extend(core.split()[overlap:])
    expected = source.split()
    first = next((i for i, (a, b) in enumerate(zip(expected, rebuilt)) if a != b), None)
    if first is None and len(expected) != len(rebuilt):
        first = min(len(expected), len(rebuilt))
    return {"exact": expected == rebuilt, "source_words": len(expected),
            "reconstructed_words": len(rebuilt), "first_mismatch_word": first,
            "expected_excerpt": " ".join(expected[first:first + 12]) if first is not None else "",
            "actual_excerpt": " ".join(rebuilt[first:first + 12]) if first is not None else ""}


def analyze_records(records, source, strategy, reference_cores=None):
    """Normalisasi dua schema, lalu ukur isi, metadata, dan overlap tiap chunk."""
    if not isinstance(records, list) or not records:
        raise ValueError("Records harus list tidak kosong.")
    if strategy not in CASES:
        raise ValueError(f"Strategi tidak dikenal: {strategy}")
    texts, cores, rows, errors = [], [], [], []
    key = "text" if strategy in ("char", "token") else "content"
    section_indices = Counter()
    for number, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            errors.append(f"Chunk {number}: record bukan object.")
            record = {}
        text = record.get(key)
        if not isinstance(text, str) or not text.strip():
            errors.append(f"Chunk {number}: {key} harus string tidak kosong.")
            text = ""
        metadata = record.get("metadata", {})
        if not isinstance(metadata, dict):
            errors.append(f"Chunk {number}: metadata bukan object.")
            metadata = {}
        reference = (reference_cores[number - 1]
                     if reference_cores and number <= len(reference_cores) else None)
        prefix, core = split_overlap(text, reference) if strategy == "header_overlap" else ("", text)
        count = len(text.split())
        if strategy in ("char", "token"):
            section = record.get("content_type")
            section_name = section if isinstance(section, str) else ""
            section_indices[section_name] += 1
            expected = {
                "chunk_index": number,
                "section_chunk_index": section_indices[section_name],
                "word_count": count,
                "source": CASES["char"][1],
            }
            for field, value in expected.items():
                actual = record.get(field)
                if actual != value or (type(value) is int and type(actual) is not int):
                    errors.append(f"Chunk {number}: {field}={record.get(field)!r}, seharusnya {value!r}.")
            if section not in ("daftar_isi", "isi_utama"):
                errors.append(f"Chunk {number}: content_type tidak dikenal.")
        else:
            section_name = metadata.get("section_path", "")
            if not isinstance(section_name, str) or not section_name.strip():
                errors.append(f"Chunk {number}: section_path kosong/tidak valid.")
                section_name = ""
            headers = [metadata[k] for k in sorted(metadata) if re.fullmatch(r"Header_[1-6]", k)]
            if not headers or not all(isinstance(h, str) and h.strip() for h in headers):
                errors.append(f"Chunk {number}: metadata Header_1..6 tidak lengkap/valid.")
            elif " > ".join(headers) != section_name:
                errors.append(f"Chunk {number}: section_path tidak sesuai hierarki header.")
        texts.append(text)
        cores.append(core)
        rows.append({
            "chunk": number,
            "words": count,
            "characters": len(text),
            "core_words": len(core.split()),
            "overlap_prefix_words": len(prefix.split()),
            "section": section_name,
            "has_source": any(isinstance(v, str) and v.strip()
                              for v in (record.get("source"), metadata.get("source"))),
            "has_page": any(type(v) is int and v > 0 for k in ("page", "page_start")
                            for v in (record.get(k), metadata.get(k))),
            "size_flag": "short" if count < MIN_WORDS else "long" if count > MAX_WORDS else "ok",
        })

    counts = [row["words"] for row in rows]
    normalized = [" ".join(text.split()) for text in texts]
    duplicates = [text for text, count in Counter(normalized).items() if count > 1 and text]
    duplicate_indices = [i + 1 for i, text in enumerate(normalized) if text in duplicates]
    # Metadata heading bukan body; ukur body Markdown dan sumber penuh terpisah.
    body_source = HEADER_LINE.sub("", source) if strategy not in ("char", "token") else source
    overlaps = []
    if strategy == "header_overlap" and texts[0].startswith("[... "):
        errors.append("Chunk 1: tidak boleh memiliki prefix overlap dari chunk sebelumnya.")
    for i in range(1, len(rows)):
        if strategy == "header_overlap":
            prefix, _ = split_overlap(texts[i], cores[i])
            previous_core = " ".join(cores[i - 1].split())
            clean_prefix = " ".join(prefix.split())
            prefix_words, previous_words = clean_prefix.split(), previous_core.split()
            valid = bool(prefix_words) and previous_words[-len(prefix_words):] == prefix_words
            overlaps.append({"chunk": i + 1, "words": len(prefix.split()), "valid": valid,
                             "cross_section": rows[i - 1]["section"] != rows[i]["section"]})
        elif strategy in ("char", "token") and rows[i - 1]["section"] == rows[i]["section"]:
            overlaps.append({"chunk": i + 1, "words": adjacent_overlap(texts[i - 1], texts[i])})

    return {
        "chunk_count": len(records),
        "schema_errors": errors,
        "word_stats": {"min": min(counts), "median": median(counts), "mean": mean(counts),
                       "max": max(counts), "total": sum(counts)},
        "short_chunks": [row["chunk"] for row in rows if row["size_flag"] == "short"],
        "long_chunks": [row["chunk"] for row in rows if row["size_flag"] == "long"],
        "duplicate_chunk_indices": duplicate_indices,
        "source_window_coverage": source_coverage(body_source, cores),
        "reconstruction": reconstruct_source(body_source, cores, [r["section"] for r in rows], strategy),
        "full_source_window_coverage": source_coverage(source, cores),
        "core_source_word_ratio": sum(len(t.split()) for t in cores) / len(body_source.split()),
        "overlap_prefix_words": sum(row["overlap_prefix_words"] for row in rows),
        "missing_source_chunks": [row["chunk"] for row in rows if not row["has_source"]],
        "missing_page_chunks": [row["chunk"] for row in rows if not row["has_page"]],
        "overlaps": overlaps,
        "chunks": rows,
    }


def compare_header_versions(base, overlapped):
    """Pastikan penambahan overlap tidak mengubah isi inti dan metadata heading."""
    errors = []
    if len(base) != len(overlapped):
        errors.append(f"Jumlah chunk berbeda: {len(base)} vs {len(overlapped)}.")
    for number, (left, right) in enumerate(zip(base, overlapped), start=1):
        if not isinstance(left, dict) or not isinstance(right, dict):
            errors.append(f"Chunk {number}: record bukan object.")
            continue
        left_text, right_text = left.get("content"), right.get("content")
        if not isinstance(left_text, str) or not isinstance(right_text, str):
            errors.append(f"Chunk {number}: content tidak valid.")
            continue
        if left_text != split_overlap(right_text, left_text)[1]:
            errors.append(f"Chunk {number}: isi inti berubah setelah overlap.")
        if left.get("metadata") != right.get("metadata"):
            errors.append(f"Chunk {number}: metadata berubah setelah overlap.")
    return errors


def audit_token_offsets(records, source, tokenizer, identity):
    """Verifikasi posisi, budget, hitungan token, dan rekonstruksi tanpa tebak overlap."""
    words, rebuilt, errors, previous_end, previous_section = source.split(), [], [], 0, None
    for i, record in enumerate(records, 1):
        if not isinstance(record, dict):
            errors.append(f"Chunk {i}: record tidak valid.")
            continue
        start, end = record.get("word_start"), record.get("word_end")
        text, budget, overlap_budget = record.get("text"), record.get("chunk_token_budget"), record.get("overlap_token_budget")
        if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(words)
                or not isinstance(text, str)):
            errors.append(f"Chunk {i}: offset/text tidak valid.")
            continue
        if start > previous_end or end <= previous_end or (i == 1 and start != 0):
            errors.append(f"Chunk {i}: gap atau urutan offset tidak maju.")
        if text.split() != words[start:end]:
            errors.append(f"Chunk {i}: teks tidak sesuai rentang sumber.")
        section = record.get("content_type")
        if section != previous_section and start < previous_end:
            errors.append(f"Chunk {i}: overlap melintasi batas section.")
        measured = count_tokens(text, tokenizer)
        measured_input = count_tokens(text, tokenizer, special=True)
        measured_overlap = count_tokens(" ".join(words[start:previous_end]), tokenizer) if start < previous_end else 0
        for field, expected in (("token_count", measured), ("input_token_count", measured_input),
                                ("overlap_tokens_before", measured_overlap)):
            if type(record.get(field)) is not int or record[field] != expected:
                errors.append(f"Chunk {i}: {field} tidak sesuai tokenizer.")
        if type(budget) is not int or budget <= 0 or measured > budget:
            errors.append(f"Chunk {i}: budget token tidak valid/terlampaui.")
        if (type(overlap_budget) is not int or type(budget) is not int
                or not 0 <= overlap_budget < budget or measured_overlap > overlap_budget):
            errors.append(f"Chunk {i}: budget overlap tidak valid/terlampaui.")
        if record.get("tokenizer") != identity:
            errors.append(f"Chunk {i}: identitas tokenizer berbeda dari evaluator.")
        rebuilt.extend(text.split()[max(0, previous_end - start):])
        previous_end, previous_section = end, section
    reconstruction = reconstruct_source(source, [" ".join(rebuilt)], ["all"], "header")
    return errors, reconstruction


def measure_tokens(result, records, tokenizer):
    """Tambahkan ukuran token nyata untuk seluruh strategi, tanpa truncation."""
    for row, record in zip(result["chunks"], records):
        text = (record.get("text", record.get("content", "")) if isinstance(record, dict) else "")
        text = text if isinstance(text, str) else ""
        row["tokens"] = count_tokens(text, tokenizer)
        row["input_tokens"] = count_tokens(text, tokenizer, special=True)
    counts = [r["tokens"] for r in result["chunks"]]
    result["token_stats"] = {"min": min(counts), "median": median(counts), "max": max(counts),
                             "mean": mean(counts), "total": sum(counts)}
    result["over_model_limit_chunks"] = [r["chunk"] for r in result["chunks"] if r["input_tokens"] > MODEL_INPUT_LIMIT]


def evaluate_all(output_dir=OUTPUT_DIR):
    """Audit setiap file secara independen agar satu file rusak tidak memblokir lainnya."""
    results, loaded = {}, {}
    tokenizer = load_tokenizer()
    identity = tokenizer_identity()
    for strategy, (filename, source_name) in CASES.items():
        result = {"file": filename, "source": source_name}
        try:
            records, strict_error = load_records(output_dir / filename)
            source = (output_dir / source_name).read_text(encoding="utf-8-sig")
            reference = ([r.get("content") if isinstance(r, dict) else None
                          for r in loaded["header"]]
                         if strategy == "header_overlap" and "header" in loaded else None)
            result.update(analyze_records(records, source, strategy, reference))
            measure_tokens(result, records, tokenizer)
            if strategy == "token":
                token_errors, result["reconstruction"] = audit_token_offsets(records, source, tokenizer, identity)
                result["schema_errors"].extend(token_errors)
            result["strict_json_error"] = strict_error
            loaded[strategy] = records
        except (OSError, UnicodeError, ValueError) as error:
            result["fatal_error"] = str(error)
        results[strategy] = result
    comparison = (compare_header_versions(loaded["header"], loaded["header_overlap"])
                  if "header" in loaded and "header_overlap" in loaded
                  else ["Perbandingan tidak tersedia karena input gagal dibaca."])
    return {"settings": {"min_words": MIN_WORDS, "max_words": MAX_WORDS,
                         "window_words": WINDOW_WORDS,
                         "minimum_coverage": MIN_SOURCE_WINDOW_COVERAGE,
                         "chunk_token_budget": CHUNK_TOKENS, "overlap_token_budget": OVERLAP_TOKENS,
                         "tokenizer": identity, "model_input_limit": MODEL_INPUT_LIMIT},
            "results": results, "header_core_comparison_errors": comparison}


def markdown_report(report):
    """Ringkas metrik dan lokasi masalah; detail setiap chunk ada di laporan JSON."""
    lines = ["# Hasil audit kualitas chunking", "",
             "Audit statis terhadap sumber ekstraksi masing-masing, bukan PDF asli atau kualitas retrieval.",
             "Ukuran kata dan token BGE-M3 diukur terpisah. Tidak ada skor gabungan/pemenang otomatis.", "",
             "| Strategi | Chunk | Kata min/median/max | Pendek | Panjang | Coverage body 5-kata | JSON standar |",
             "| --- | ---: | --- | ---: | ---: | ---: | --- |"]
    for name, result in report["results"].items():
        if "fatal_error" in result:
            lines.append(f"| {name} | - | - | - | - | - | GAGAL BACA |")
            continue
        stats = result["word_stats"]
        state = "GAGAL" if result["strict_json_error"] else "LULUS"
        coverage = result["source_window_coverage"]["ratio"]
        lines.append(f"| {name} | {result['chunk_count']} | {stats['min']}/{stats['median']:g}/{stats['max']} | "
                     f"{len(result['short_chunks'])} | {len(result['long_chunks'])} | {coverage:.2%} | {state} |")
    for name, result in report["results"].items():
        lines += ["", f"## {name}", "", f"Sumber: `{result['source']}`.", ""]
        if "fatal_error" in result:
            lines.append(f"Gagal: {result['fatal_error']}")
            continue
        lines += [f"- JSON ketat: {result['strict_json_error'] or 'valid'}.",
                  f"- Token BGE-M3 min/median/max: {result['token_stats']['min']}/{result['token_stats']['median']}/{result['token_stats']['max']} (tanpa special tokens).",
                  f"- Chunk melewati {MODEL_INPUT_LIMIT} token termasuk special tokens: {result['over_model_limit_chunks']}.",
                  f"- Error schema: {len(result['schema_errors'])}; {result['schema_errors'][:8]}.",
                  f"- Chunk pendek (< {MIN_WORDS} kata): {result['short_chunks']}.",
                  f"- Chunk panjang (> {MAX_WORDS} kata): {result['long_chunks']}.",
                  f"- Chunk duplikat persis setelah normalisasi whitespace: {result['duplicate_chunk_indices']}.",
                  f"- Chunk tanpa nama sumber: {result['missing_source_chunks']}.",
                  f"- Chunk tanpa halaman: {result['missing_page_chunks']}.",
                  f"- Rasio jumlah kata inti / kata sumber body: {result['core_source_word_ratio']:.3f} (bukan skor).",
                  f"- Total kata prefix overlap: {result['overlap_prefix_words']}.",
                  f"- Rekonstruksi urutan kata sumber: {'IDENTIK' if result['reconstruction']['exact'] else 'BERBEDA'} "
                  f"({result['reconstruction']['reconstructed_words']}/{result['reconstruction']['source_words']} kata).",
                  f"- Coverage sumber penuh termasuk heading: {result['full_source_window_coverage']['ratio']:.2%}.",
                  f"- Contoh window body tidak ditemukan: {result['source_window_coverage']['missing_examples']}."]
        if result["overlaps"]:
            sizes = [item["words"] for item in result["overlaps"]]
            lines.append(f"- Overlap bersebelahan (kata) min/median/max: {min(sizes)}/{median(sizes):g}/{max(sizes)}.")
        if name == "header_overlap":
            invalid = [item["chunk"] for item in result["overlaps"] if not item["valid"]]
            crossing = sum(item["cross_section"] for item in result["overlaps"])
            lines += [f"- Prefix bukan suffix isi inti sebelumnya: {invalid}.",
                      f"- Overlap antar-section: {crossing} pasangan (perlu tinjauan konteks)."]
    lines += ["", "## Konsistensi versi heading", "",
              str(report["header_core_comparison_errors"] or "Isi inti dan metadata identik pada kedua versi."),
              "", "## Cara membaca", "",
              "Coverage menguji window kata sumber yang muncul utuh di suatu chunk. Whitespace dinormalisasi; "
              "huruf dan tanda baca dipertahankan. Window berulang dapat cocok pada lokasi lain. "
              "Batas chunk tanpa overlap dapat mengurangi coverage walaupun semua kata tersimpan.",
              "", "Untuk heading, coverage body mengabaikan baris heading sumber dan wrapper overlap. "
              "Coverage penuh tidak memasukkan metadata heading sehingga lebih rendah belum tentu kehilangan isi. "
              "Sumber TXT bersih dan Markdown berbeda; persentase antar-strategi tidak menentukan pemenang langsung.",
              "", f"Batas {MIN_WORDS}–{MAX_WORDS} kata adalah penanda tinjauan; chunk pendek bisa valid. "
              f"Coverage di bawah {MIN_SOURCE_WINDOW_COVERAGE:.0%} adalah penanda tinjauan, bukan kegagalan kehilangan isi. "
              "Gate kelengkapan memakai rekonstruksi urutan kata; pada word chunk diasumsikan overlap suffix-prefix terpanjang dalam section sama. "
              "Kecocokan makna, integritas tabel, nomor halaman asli, dan jawaban RAG tetap perlu evaluasi terpisah.",
              "", "Untuk memilih strategi, gunakan pertanyaan berjawaban acuan dan sumber benar, lalu bandingkan "
              "Recall@k, peringkat setelah reranking, dan ketepatan kutipan memakai model/config yang sama."]
    return "\n".join(lines) + "\n"


def main():
    """Tulis laporan saja; tidak menjalankan ulang chunker atau mengubah input."""
    report = evaluate_all()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "chunking_quality.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORT_DIR / "chunking_quality.md").write_text(markdown_report(report), encoding="utf-8")
    from visualize_chunking import render_dashboard
    render_dashboard(report, REPORT_DIR / "chunking_quality.html")
    for name, result in report["results"].items():
        if "fatal_error" in result:
            print(f"{name}: GAGAL BACA - {result['fatal_error']}")
        else:
            state = "GAGAL" if result["strict_json_error"] else "LULUS"
            print(f"{name}: {result['chunk_count']} chunk; JSON {state}; "
                  f"coverage body {result['source_window_coverage']['ratio']:.2%}; "
                  f"pendek {len(result['short_chunks'])}; panjang {len(result['long_chunks'])}")
    print(f"Laporan: {REPORT_DIR}")
    print("Exit 0 berarti laporan selesai. Jalankan unittest untuk status quality gate.")


if __name__ == "__main__":
    main()
