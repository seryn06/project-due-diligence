import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import search_epmc as ep

R = {"id": "123", "source": "MED", "doi": "10.3/z", "title": "T", "authorString": "A, B",
     "journalTitle": "Plant J", "pubYear": "2022", "abstractText": "<p>abs</p>",
     "citedByCount": 4, "pubType": ["review"], "isOpenAccess": "Y",
     "fullTextUrlList": {"fullTextUrl": [{"url": "http://ft", "documentStyle": "pdf"}]}}

class TestEpmc(unittest.TestCase):
    def test_normalize(self):
        r = ep.normalize(R)
        self.assertEqual((r["source_id"], r["doi"], r["paper_type"]), ("MED:123", "10.3/z", "review"))
        self.assertEqual(r["authors"], ["A", "B"])
        self.assertEqual(r["abstract"], "abs")
        self.assertEqual(r["oa_url"], "http://ft")
        self.assertEqual(r["year"], 2022)

    def test_compose_query(self):
        q = ep.compose_query("rag", 2020, 2026)
        self.assertIn("rag", q); self.assertIn("PUB_YEAR:[2020 TO 2026]", q)
        self.assertEqual(ep.compose_query("rag", None, None), "rag")

if __name__ == "__main__":
    unittest.main()
