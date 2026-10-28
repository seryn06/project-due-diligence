import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import search_openalex as oa

class TestNormalize(unittest.TestCase):
    def test_normalize_full(self):
        w = {"id": "https://openalex.org/W123", "title": "A Study", "publication_year": 2024,
             "doi": "https://doi.org/10.1/x", "cited_by_count": 7, "type": "review",
             "authorships": [{"author": {"display_name": "Alice"}}],
             "primary_location": {"source": {"display_name": "Nature"}, "pdf_url": "http://p.pdf"},
             "abstract_inverted_index": {"Hello": [0], "world": [1]}}
        r = oa.normalize(w)
        self.assertEqual(r["source"], "openalex")
        self.assertEqual(r["source_id"], "W123")
        self.assertEqual(r["doi"], "10.1/x")
        self.assertEqual(r["paper_type"], "review")
        self.assertEqual(r["abstract"], "Hello world")
        self.assertEqual(r["venue"], "Nature")
        self.assertEqual(r["oa_url"], "http://p.pdf")
        self.assertEqual(r["year"], 2024)

    def test_normalize_empty(self):
        r = oa.normalize({})
        self.assertEqual(r["title"], "")
        self.assertEqual(r["paper_type"], "other")

class TestPagination(unittest.TestCase):
    def test_search_pages_and_stops(self):
        pages = [{"meta": {"next_cursor": "c2"}, "results": [{"id": f"https://openalex.org/W{i}"} for i in range(50)]},
                 {"meta": {"next_cursor": None},
                  "results": [{"id": f"https://openalex.org/W{50 + i}"} for i in range(10)]}]
        state = {"i": 0}
        def fake_fetch(url, params=None, **kw):
            p = pages[state["i"]]; state["i"] += 1; return p
        orig = oa.lib.fetch_json; oa.lib.fetch_json = fake_fetch
        try:
            out = oa.search("q", limit=60)
        finally:
            oa.lib.fetch_json = orig
        self.assertEqual(len(out), 60)

class TestCitationExpansion(unittest.TestCase):
    def test_cited_by(self):
        def fake(url, params=None, **kw):
            assert "cites:W123" in params.get("filter", ""), params
            return {"meta": {"next_cursor": None}, "results": [{"id": "https://openalex.org/W9"}]}
        orig = oa.lib.fetch_json; oa.lib.fetch_json = fake
        try:
            out = oa.cited_by("W123", limit=10)
        finally:
            oa.lib.fetch_json = orig
        self.assertEqual(len(out), 1)

    def test_refs_of_batches(self):
        def fake(url, params=None, **kw):
            if url.endswith("/works/W123"):
                return {"referenced_works": [f"W{i}" for i in range(1, 201)]}
            assert params.get("filter", "").startswith("openalex:W"), params
            assert len(params["filter"].split("|")) <= 100
            return {"meta": {"next_cursor": None},
                    "results": [{"id": f"https://openalex.org/W{i}"} for i in range(1, 101)]}
        orig = oa.lib.fetch_json; oa.lib.fetch_json = fake
        try:
            out = oa.refs_of("W123", limit=150)
        finally:
            oa.lib.fetch_json = orig
        self.assertEqual(len(out), 150)   # 200 refs -> 两批100，截到 limit

if __name__ == "__main__":
    unittest.main()
