import sys, pathlib, os, json, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import lib

class TestNorm(unittest.TestCase):
    def test_norm_doi(self):
        self.assertEqual(lib.norm_doi("https://doi.org/10.1/x"), "10.1/x")
        self.assertEqual(lib.norm_doi("DOI:10.1/X "), "10.1/x")
        self.assertEqual(lib.norm_doi(""), "")

    def test_norm_title(self):
        self.assertEqual(lib.norm_title("Hello, World!"), "helloworld")
        self.assertEqual(lib.norm_title("Café— naïve"), "cafenave")

class TestJsonIO(unittest.TestCase):
    def test_roundtrip_missing(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.json")
            self.assertIsNone(lib.load_json(p))
            lib.save_json(p, {"x": 1})
            self.assertEqual(lib.load_json(p), {"x": 1})

class TestSearchLog(unittest.TestCase):
    def test_append(self):
        with tempfile.TemporaryDirectory() as d:
            id1 = lib.append_search_log(d, {"source": "openalex", "query": "q", "path": "综述",
                                            "question_id": "Q1", "purpose": "", "result_count": 3})
            id2 = lib.append_search_log(d, {"source": "arxiv", "query": "q2", "path": "前沿",
                                            "question_id": "Q1", "purpose": "", "result_count": 1})
            self.assertEqual((id1, id2), ("S001", "S002"))
            log = lib.load_json(os.path.join(d, "search_log.json"))
            self.assertEqual(len(log), 2)
            self.assertTrue(log[0]["ts"])

class TestRecords(unittest.TestCase):
    def test_load_records(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "raw"))
            lib.save_json(os.path.join(d, "raw", "a_1.json"), [{"title": "t"}])
            lib.save_json(os.path.join(d, "raw", "b_2.json"), [{"title": "u"}])
            self.assertEqual(len(lib.load_records(d)), 2)

    def test_default_entry(self):
        e = lib.default_entry({"source": "x", "doi": "", "title": "T", "year": 2024, "abstract": "abs",
                               "oa_url": "", "authors": [], "venue": "", "citation_count": 0,
                               "source_id": "1", "paper_type": "article"})
        self.assertEqual(e["access_status"], "仅摘要")
        self.assertEqual(e["reading_status"], "待筛")
        self.assertEqual(e["reading_level"], "L1")
        self.assertEqual(e["question_ids"], [])

class TestFetchBackoff(unittest.TestCase):
    def test_retry_then_success(self):
        import urllib.error, io
        calls = {"n": 0}
        def fake_urlopen(req, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise urllib.error.HTTPError(req.full_url, 429, "rate", {}, io.BytesIO(b""))
            return io.BytesIO(json.dumps({"ok": 1}).encode())
        orig = lib.urllib.request.urlopen
        lib.urllib.request.urlopen = fake_urlopen
        orig_sleep = lib.time.sleep
        lib.time.sleep = lambda s: None
        try:
            self.assertEqual(lib.fetch_json("http://x.test/api", retries=3), {"ok": 1})
            self.assertEqual(calls["n"], 2)
        finally:
            lib.urllib.request.urlopen = orig
            lib.time.sleep = orig_sleep

class TestTokenOverlap(unittest.TestCase):
    def test_overlap(self):
        self.assertGreaterEqual(lib.token_overlap("Attention is all you need",
                                                  "Attention Is All You Need!"), 0.99)
        self.assertLess(lib.token_overlap("cats dogs", "boats ships"), 0.5)

if __name__ == "__main__":
    unittest.main()
