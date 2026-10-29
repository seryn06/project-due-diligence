import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import search_s2 as s2

P = {"paperId": "abc", "title": "T", "abstract": "A", "year": 2023,
     "authors": [{"name": "Bob"}], "venue": "NeurIPS", "citationCount": 5,
     "externalIds": {"DOI": "10.2/y"}, "publicationTypes": ["Review"],
     "openAccessPdf": {"url": "http://x.pdf"}}

class TestNormalize(unittest.TestCase):
    def test_review(self):
        r = s2.normalize(P)
        self.assertEqual((r["source"], r["source_id"], r["doi"], r["paper_type"]),
                         ("s2", "abc", "10.2/y", "review"))
        self.assertEqual(r["oa_url"], "http://x.pdf")

    def test_article_no_doi(self):
        q = dict(P); q.pop("externalIds"); q["publicationTypes"] = []
        r = s2.normalize(q)
        self.assertEqual((r["paper_type"], r["doi"]), ("article", ""))

class TestExpand(unittest.TestCase):
    def test_refs_and_cites(self):
        def fake(url, params=None, **kw):
            if url.endswith("/references"):
                return {"data": [{"citedPaper": P}], "next": None}
            return {"data": [{"citingPaper": P}], "next": None}
        orig = s2.lib.fetch_json; s2.lib.fetch_json = fake
        try:
            self.assertEqual(len(s2.expand("abc", "refs")), 1)
            self.assertEqual(len(s2.expand("abc", "cites")), 1)
        finally:
            s2.lib.fetch_json = orig

class TestSearchPagination(unittest.TestCase):
    def test_search_stops_at_total(self):
        def fake(url, params=None, **kw):
            return {"total": 3, "data": [P, P, P], "next": None}
        orig = s2.lib.fetch_json; s2.lib.fetch_json = fake
        try:
            out = s2.search("q", limit=100)
        finally:
            s2.lib.fetch_json = orig
        self.assertEqual(len(out), 3)

if __name__ == "__main__":
    unittest.main()
