import sys, pathlib, os, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tests"))
import lib, gatefix, compare_runs

def _one_sided(doi_or_title):
    """构造单侧有 DOI 的同名文献，验证双键匹配"""
    return doi_or_title

class TestCompare(unittest.TestCase):
    def test_overlap_dual_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = gatefix.fresh(os.path.join(tmp, "a"))
            b = gatefix.fresh(os.path.join(tmp, "b"))
            # b：把 P001 换成同题名无 DOI 版本（单键匹配会漏的双键场景）+ 追加一篇独有
            cat = lib.load_json(os.path.join(b, "catalog.json"))
            cat[0]["doi"] = ""
            cat.append({**cat[1], "paper_id": "P999", "doi": "10.9/9", "title": "Only In B"})
            lib.save_json(os.path.join(b, "catalog.json"), cat)
            res = compare_runs.compare(a, b)
            self.assertEqual(res["a"]["shared"], res["a"]["included"])   # A 全部在 B 中找到
            self.assertEqual(res["b"]["unique"], 1)
            self.assertEqual(res["b_only_top"][0]["title"], "Only In B")

    def test_zero_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = gatefix.fresh(os.path.join(tmp, "a"))
            b = gatefix.fresh(os.path.join(tmp, "b"))
            cat = lib.load_json(os.path.join(b, "catalog.json"))
            for i, r in enumerate(cat):
                r["doi"] = f"10.z/{i}"
                r["title"] = f"Different Paper {i}"
            lib.save_json(os.path.join(b, "catalog.json"), cat)
            res = compare_runs.compare(a, b)
            self.assertEqual(res["a"]["overlap_pct"], 0.0)
            self.assertEqual(res["b"]["overlap_pct"], 0.0)

if __name__ == "__main__":
    unittest.main()
