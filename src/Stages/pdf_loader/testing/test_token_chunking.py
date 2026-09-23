"""Pengujian tokenizer asli, pembatasan budget, dan integrasi strategi keempat."""

import copy
import unittest

# Evaluator menambahkan path stage sehingga modul dapat dijalankan dari VS Code.
from evaluate_chunking import audit_token_offsets, evaluate_all
from chunking_token import (
    build_records, chunk_by_tokens, count_tokens, load_tokenizer, tokenizer_identity,
)


class TestTokenChunking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Muat tokenizer sekali dari cache lokal; tidak melakukan download."""
        cls.tokenizer = load_tokenizer()
        cls.identity = tokenizer_identity()

    def test_real_subword_tokens_are_not_word_count(self):
        text = "Ketidakberkesinambungan pengembangan sistem perusahaan."
        self.assertGreater(count_tokens(text, self.tokenizer), len(text.split()))
        self.assertGreater(count_tokens(text, self.tokenizer, special=True),
                           count_tokens(text, self.tokenizer))

    def test_budget_unicode_offsets_and_forward_progress(self):
        text = "Cuti tahunan café 東京 karyawan 🙂 sesuai prosedur perusahaan. " * 12
        words = text.split()
        for budget, overlap in ((32, 0), (32, 8), (32, 31)):
            with self.subTest(budget=budget, overlap=overlap):
                chunks = chunk_by_tokens(text, self.tokenizer, budget, overlap)
                self.assertGreater(len(chunks), 1)
                rebuilt, previous_end = [], 0
                for chunk in chunks:
                    start, end = chunk["word_start"], chunk["word_end"]
                    self.assertGreater(end, previous_end)
                    self.assertLessEqual(start, previous_end)
                    self.assertEqual(chunk["text"].split(), words[start:end])
                    self.assertLessEqual(count_tokens(chunk["text"], self.tokenizer), budget)
                    self.assertLessEqual(chunk["overlap_tokens_before"], overlap)
                    rebuilt.extend(chunk["text"].split()[previous_end - start:])
                    previous_end = end
                self.assertEqual(rebuilt, words)

    def test_invalid_budget_and_overlap(self):
        for budget, overlap in ((0, 0), (True, 0), (10, -1), (10, 10), (10, 1.5)):
            with self.subTest(budget=budget, overlap=overlap):
                with self.assertRaises(ValueError):
                    chunk_by_tokens("isi", self.tokenizer, budget, overlap)

    def test_empty_and_short_input(self):
        self.assertEqual(chunk_by_tokens("  \n", self.tokenizer), [])
        chunks = chunk_by_tokens("satu kalimat pendek", self.tokenizer)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["overlap_tokens_before"], 0)

    def test_single_oversized_word_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, "melebihi budget"):
            chunk_by_tokens("ketidakberkesinambungan", self.tokenizer, budget=1, overlap=0)

    def test_sections_and_exact_offset_reconstruction(self):
        source = "DAFTAR ISI\n1. PENDAHULUAN\n" + "Pengembangan sistem lokal. " * 700
        records = build_records(source, self.tokenizer, self.identity)
        self.assertEqual({r["content_type"] for r in records}, {"daftar_isi", "isi_utama"})
        first_body = next(r for r in records if r["content_type"] == "isi_utama")
        self.assertEqual(first_body["overlap_tokens_before"], 0)
        errors, reconstruction = audit_token_offsets(records, source, self.tokenizer, self.identity)
        self.assertEqual(errors, [])
        self.assertTrue(reconstruction["exact"])

    def test_corrupted_counts_offsets_and_identity_are_detected(self):
        source = "DAFTAR ISI\n1. PENDAHULUAN\nInformasi perusahaan."
        records = build_records(source, self.tokenizer, self.identity)
        for field, value in (("token_count", 999), ("input_token_count", True),
                             ("word_start", 1), ("tokenizer", {}), ("overlap_token_budget", -1)):
            with self.subTest(field=field):
                broken = copy.deepcopy(records)
                broken[0][field] = value
                errors, _ = audit_token_offsets(broken, source, self.tokenizer, self.identity)
                self.assertTrue(errors)

    def test_all_four_artifacts_have_real_token_metrics(self):
        report = evaluate_all()
        self.assertEqual(set(report["results"]), {"char", "header", "header_overlap", "token"})
        for name, result in report["results"].items():
            with self.subTest(strategy=name):
                self.assertNotIn("fatal_error", result)
                self.assertGreater(result["token_stats"]["max"], 0)
                self.assertTrue(all(r["input_tokens"] >= r["tokens"] for r in result["chunks"]))
        token_result = report["results"]["token"]
        self.assertEqual(token_result["schema_errors"], [])
        self.assertTrue(token_result["reconstruction"]["exact"])

    def test_all_artifacts_fit_bge_model_input_limit(self):
        for name, result in evaluate_all()["results"].items():
            with self.subTest(strategy=name):
                self.assertNotIn("fatal_error", result)
                self.assertEqual(result["over_model_limit_chunks"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
