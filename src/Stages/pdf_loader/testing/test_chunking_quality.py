"""Unit test evaluator + quality gate tiga JSON aktual; jalankan dari VS Code/terminal."""

import json
import tempfile
import unittest
from pathlib import Path

from evaluate_chunking import (
    adjacent_overlap,
    analyze_records,
    compare_header_versions,
    evaluate_all,
    load_records,
    source_coverage,
    split_overlap,
    reconstruct_source,
    windows,
)
from visualize_chunking import render_dashboard


class TestQualityMetrics(unittest.TestCase):
    """Kasus kecil dengan jawaban pasti untuk memverifikasi alat ukurnya."""

    def test_complete_source_with_overlap(self):
        result = source_coverage("a b c d e f g", ["a b c d e f", "c d e f g"])
        self.assertEqual(result["ratio"], 1.0)

    def test_reconstruction_does_not_confuse_boundary_with_lost_content(self):
        source = "a b c d e f g h"
        chunks = ["a b c d", "e f g h"]
        self.assertLess(source_coverage(source, chunks)["ratio"], 1)
        self.assertTrue(reconstruct_source(source, chunks, ["A", "B"], "header")["exact"])

    def test_reconstruction_detects_lost_repeated_passage(self):
        source = "a b c d e a b c d e"
        chunks = ["a b c d e"]
        # Set-based coverage alone misses the lost second occurrence.
        self.assertFalse(reconstruct_source(source, chunks, ["A"], "header")["exact"])

    def test_reconstruction_detects_reordering_and_extra_words(self):
        for chunks in (["c d", "a b"], ["a b", "c d extra"]):
            with self.subTest(chunks=chunks):
                self.assertFalse(reconstruct_source("a b c d", chunks, ["A", "B"], "header")["exact"])

    def test_word_reconstruction_respects_section_boundaries(self):
        self.assertTrue(reconstruct_source("a b c d", ["a b c", "b c d"],
                                           ["A", "A"], "char")["exact"])
        self.assertTrue(reconstruct_source("a b b c", ["a b", "b c"],
                                           ["A", "B"], "char")["exact"])

    def test_invalid_analysis_inputs_have_clear_errors(self):
        for records, strategy in (([], "char"), ({}, "header"), ([{}], "typo")):
            with self.subTest(records=records, strategy=strategy):
                with self.assertRaises(ValueError):
                    analyze_records(records, "source", strategy)
        for width in (0, -1, True, 1.5):
            with self.subTest(width=width):
                with self.assertRaises(ValueError):
                    windows(["word"], width)

    def test_bool_is_not_valid_integer_metadata(self):
        row = {"text": "isi", "word_count": True, "chunk_index": True,
               "section_chunk_index": True, "source": "Pedoman PI_cleaned.txt",
               "content_type": "isi_utama", "page": True}
        result = analyze_records([row], "isi", "char")
        self.assertEqual(len(result["schema_errors"]), 3)
        self.assertEqual(result["missing_page_chunks"], [1])

    def test_overlap_must_match_whole_words(self):
        records = [{"content": "pelaksanaan", "metadata": {}},
                   {"content": "[... anaan]\n\nlanjut", "metadata": {}}]
        result = analyze_records(records, "pelaksanaan lanjut", "header_overlap")
        self.assertFalse(result["overlaps"][0]["valid"])

    def test_first_chunk_must_not_have_overlap(self):
        result = analyze_records([{"content": "[... asing]\n\nisi", "metadata": {
            "Header_1": "A", "section_path": "A"}}], "isi", "header_overlap")
        self.assertTrue(any("Chunk 1" in error for error in result["schema_errors"]))

    def test_nonstandard_json_numbers_and_duplicate_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            for raw in ('[{"text": NaN}]', '[{"text": Infinity}]',
                        '[{"text": "a", "text": "b"}]'):
                with self.subTest(raw=raw):
                    path.write_text(raw, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_records(path)

    def test_dashboard_embeds_data_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = {"danger": "</script><img src=x onerror=alert(1)>"}
            path = render_dashboard(payload, Path(directory) / "report.html")
            html = path.read_text(encoding="utf-8")
            self.assertNotIn(payload["danger"], html)
            self.assertNotIn("__REPORT_JSON__", html)
            data = html.split('<script id="report-data" type="application/json">')[1].split('</script>')[0]
            self.assertEqual(json.loads(data), payload)

    def test_one_missing_artifact_does_not_block_other_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "Pedoman PI.md").write_text("# A\nisi", encoding="utf-8")
            row = [{"content": "isi", "metadata": {"Header_1": "A", "section_path": "A"}}]
            (path / "Pedoman PI_chunks_header.json").write_text(json.dumps(row), encoding="utf-8")
            report = evaluate_all(path)
            self.assertIn("fatal_error", report["results"]["char"])
            self.assertNotIn("fatal_error", report["results"]["header"])
            self.assertTrue(report["header_core_comparison_errors"])

    def test_missing_middle_is_detected(self):
        result = source_coverage("a b c d e f g h i j", ["a b c d e", "g h i j"])
        self.assertLess(result["ratio"], 1.0)
        self.assertGreater(result["missing_windows"], 0)

    def test_words_in_wrong_order_do_not_pass(self):
        result = source_coverage("a b c d e", ["e d c b a"])
        self.assertEqual(result["ratio"], 0.0)

    def test_source_whitespace_does_not_change_coverage(self):
        self.assertEqual(source_coverage("a\n b\t c d e", ["a b c d e"])["ratio"], 1.0)

    def test_short_source_and_empty_source(self):
        self.assertEqual(source_coverage("dua kata", ["dua kata lain"])["ratio"], 1.0)
        self.assertEqual(source_coverage("dua kata", ["dua"])["ratio"], 0.0)
        with self.assertRaises(ValueError):
            source_coverage("", ["isi"])

    def test_overlap_must_be_suffix_prefix(self):
        self.assertEqual(adjacent_overlap("satu dua tiga", "dua tiga empat"), 2)
        self.assertEqual(adjacent_overlap("dua satu tiga", "dua empat"), 0)

    def test_wrapper_preserves_core(self):
        self.assertEqual(split_overlap("[... isi sebelumnya]\n\nisi baru"),
                         ("isi sebelumnya", "isi baru"))
        self.assertEqual(split_overlap("isi biasa [dengan kurung]"),
                         ("", "isi biasa [dengan kurung]"))

    def test_copied_closing_marker_does_not_look_like_changed_core(self):
        text = "[... lama]\n\nsebelumnya]\n\ninti"
        self.assertEqual(split_overlap(text, "inti"), ("lama]\n\nsebelumnya", "inti"))
        base = [{"content": "inti", "metadata": {}}]
        self.assertEqual(compare_header_versions(base, [{"content": text, "metadata": {}}]), [])

    def test_strict_json_error_survives_diagnostic_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.json"
            text = '_comment catatan\n[{"text": "isi"}]'
            path.write_text(text, encoding="utf-8")
            records, error = load_records(path)
            self.assertIsNotNone(error)
            self.assertEqual(records, [{"text": "isi"}])
            self.assertEqual(path.read_text(encoding="utf-8"), text)

    def test_invalid_roots_and_other_json_corruption_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.json"
            for content in ("[]", "{}", "null", "not json", "[broken]"):
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_records(path)

    def test_valid_json_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.json"
            path.write_text(json.dumps([{"content": "isi"}]), encoding="utf-8")
            self.assertIsNone(load_records(path)[1])

    def test_schema_errors_and_duplicate_chunks_are_detected(self):
        records = [{"content": "satu dua tiga empat lima", "metadata": {}},
                   {"content": "satu dua tiga empat lima", "metadata": {}},
                   {"content": "", "metadata": []}, "invalid"]
        result = analyze_records(records, "satu dua tiga empat lima", "header")
        self.assertTrue(result["schema_errors"])
        self.assertEqual(result["duplicate_chunk_indices"], [1, 2])

    def test_heading_metadata_not_counted_as_missing_body(self):
        records = [{"content": "satu dua tiga empat lima", "metadata": {
            "Header_1": "Judul", "section_path": "Judul"}}]
        result = analyze_records(records, "# Judul\nsatu dua tiga empat lima", "header")
        self.assertEqual(result["source_window_coverage"]["ratio"], 1.0)
        self.assertFalse(result["schema_errors"])

    def test_changed_core_or_metadata_is_detected(self):
        base = [{"content": "isi asli", "metadata": {"section_path": "A"}}]
        good = [{"content": "[... sebelumnya]\n\nisi asli", "metadata": {"section_path": "A"}}]
        bad = [{"content": "isi diganti", "metadata": {"section_path": "B"}}]
        self.assertEqual(compare_header_versions(base, good), [])
        self.assertEqual(len(compare_header_versions(base, bad)), 2)

    def test_propagated_overlap_is_flagged(self):
        records = [
            {"content": "[... lama]\n\nbaru", "metadata": {"Header_1": "A", "section_path": "A"}},
            {"content": "[... [... lama] baru]\n\nlanjut", "metadata": {"Header_1": "B", "section_path": "B"}},
        ]
        result = analyze_records(records, "baru lanjut", "header_overlap")
        self.assertFalse(result["overlaps"][0]["valid"])


class TestChunkArtifacts(unittest.TestCase):
    """Gate data aktual. Kegagalan menunjukkan masalah input, bukan selalu bug test."""

    @classmethod
    def setUpClass(cls):
        """Baca artefak sekali; semua test menggunakan snapshot audit yang sama."""
        cls.report = evaluate_all()

    def test_files_are_readable(self):
        for name, result in self.report["results"].items():
            with self.subTest(strategy=name):
                self.assertNotIn("fatal_error", result, result.get("fatal_error"))

    def test_strict_json(self):
        for name, result in self.report["results"].items():
            with self.subTest(strategy=name):
                self.assertNotIn("fatal_error", result, result.get("fatal_error"))
                self.assertIsNone(result["strict_json_error"],
                                  f"{result['file']}: {result['strict_json_error']}")

    def test_schema_and_nonempty_content(self):
        for name, result in self.report["results"].items():
            with self.subTest(strategy=name):
                self.assertNotIn("fatal_error", result, result.get("fatal_error"))
                self.assertEqual(result["schema_errors"], [])

    def test_no_exact_duplicate_chunks(self):
        for name, result in self.report["results"].items():
            with self.subTest(strategy=name):
                self.assertNotIn("fatal_error", result, result.get("fatal_error"))
                self.assertEqual(result["duplicate_chunk_indices"], [])

    def test_source_reconstruction(self):
        for name, result in self.report["results"].items():
            with self.subTest(strategy=name):
                self.assertNotIn("fatal_error", result, result.get("fatal_error"))
                self.assertTrue(result["reconstruction"]["exact"], result["reconstruction"])

    def test_header_overlap_preserves_core_and_metadata(self):
        self.assertEqual(self.report["header_core_comparison_errors"], [])

    def test_overlap_does_not_propagate_foreign_content(self):
        result = self.report["results"]["header_overlap"]
        self.assertNotIn("fatal_error", result, result.get("fatal_error"))
        invalid = [item["chunk"] for item in result["overlaps"] if not item["valid"]]
        self.assertEqual(invalid, [], f"Prefix tidak berasal dari suffix inti sebelumnya: {invalid}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
