import sys, pathlib, unittest
import xml.etree.ElementTree as ET
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import search_arxiv as ax

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2401.00001v1</id>
    <title>Paper  Title </title>
    <summary> Sum of work. </summary>
    <published>2024-01-02T00:00:00Z</published>
    <author><name>Carol</name></author>
    <link rel="alternate" href="http://arxiv.org/abs/2401.00001"/>
    <link title="pdf" rel="related" type="application/pdf" href="http://arxiv.org/pdf/2401.00001"/>
    <arxiv:doi>10.4/w</arxiv:doi>
  </entry>
</feed>"""

class TestArxiv(unittest.TestCase):
    def test_compose(self):
        self.assertEqual(ax.compose_query("agent evaluation"), "all:agent AND all:evaluation")

    def test_normalize(self):
        root = ET.fromstring(ATOM)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        e = root.find("a:entry", ns)
        r = ax.normalize(e)
        self.assertEqual(r["source"], "arxiv")
        self.assertEqual(r["source_id"], "2401.00001")
        self.assertEqual(r["title"], "Paper Title")
        self.assertEqual(r["year"], 2024)
        self.assertEqual(r["paper_type"], "preprint")
        self.assertEqual(r["doi"], "10.4/w")
        self.assertTrue(r["oa_url"].endswith(".00001"))

    def test_search_pagination(self):
        entries = ET.fromstring(ATOM).findall("{http://www.w3.org/2005/Atom}entry")
        def fake_text(url, params=None, **kw):
            return ATOM
        orig = ax.lib.fetch_text; ax.lib.fetch_text = fake_text
        try:
            out = ax.search("agent evaluation", limit=50)
        finally:
            ax.lib.fetch_text = orig
        self.assertEqual(len(out), 1)   # 1 entry < page size → 停

if __name__ == "__main__":
    unittest.main()
