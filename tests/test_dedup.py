import sys, pathlib, os, json, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import lib, dedup

def rec(**kw):
    base = {"source": "openalex", "source_id": "W1", "doi": "", "title": "T", "year": 2024,
            "authors": [], "venue": "", "abstract": "", "citation_count": 0,
            "oa_url": "", "paper_type": "article"}
    base.update(kw)
    return base

class TestMerge(unittest.TestCase):
    def test_doi_merge_richest_wins(self):
        a = rec(source="openalex", doi="10.1/x", title="Same Paper", abstract="long abstract " * 5,
                citation_count=3, venue="V")
        b = rec(source="s2", doi="10.1/X", title="same  paper!", abstract="", citation_count=9)
        merged, log = dedup.merge_records([a, b])
        self.assertEqual(len(merged), 1)
        m = merged[0]
        self.assertEqual(m["citation_count"], 9)      # s2 记录分高
        self.assertEqual(m["venue"], "V")             # 空字段回填
        self.assertEqual(m["n_sources"], 2)
        self.assertEqual(m["paper_id"], "P001")
        self.assertEqual(log[0]["n_merged"], 2)

    def test_title_merge_no_doi(self):
        a = rec(title="Café Study")
        b = rec(source="epmc", title="cafe study")
        merged, _ = dedup.merge_records([a, b])
        self.assertEqual(len(merged), 1)

    def test_distinct_kept(self):
        merged, _ = dedup.merge_records([rec(title="A"), rec(title="B")])
        self.assertEqual(len(merged), 2)

class TestUpdateCatalog(unittest.TestCase):
    def test_preserves_manual_fields(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "raw"))
            lib.save_json(os.path.join(d, "raw", "a.json"),
                          [rec(doi="10.1/x", title="Paper One", citation_count=5)])
            lib.save_json(os.path.join(d, "catalog.json"),
                          [{"paper_id": "P001", "source": "openalex", "source_id": "W1",
                            "doi": "10.1/x", "title": "Paper One", "year": 2024, "authors": [],
                            "venue": "", "abstract": "", "citation_count": 1, "oa_url": "",
                            "paper_type": "article", "n_sources": 1, "question_ids": ["Q2"],
                            "access_status": "仅摘要", "reading_status": "纳入", "include_reason": "直接相关",
                            "exclude_reason": "", "reading_level": "L2", "first_seen": "2026-10-28"}])
            stats = dedup.update_catalog(d)
            cat = lib.load_json(os.path.join(d, "catalog.json"))
            self.assertEqual(len(cat), 1)
            self.assertEqual(cat[0]["question_ids"], ["Q2"])     # 人工字段保留
            self.assertEqual(cat[0]["reading_status"], "纳入")
            self.assertEqual(cat[0]["citation_count"], 5)          # unified 字段更新
            self.assertEqual(stats["n_new"], 0)

    def test_new_record_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "raw"))
            lib.save_json(os.path.join(d, "raw", "a.json"), [rec(title="Brand New", abstract="x")])
            dedup.update_catalog(d)
            cat = lib.load_json(os.path.join(d, "catalog.json"))
            self.assertEqual(cat[0]["reading_status"], "待筛")
            self.assertEqual(cat[0]["paper_id"], "P001")

class TestCheckMode(unittest.TestCase):
    def test_check_detects_dup(self):
        with tempfile.TemporaryDirectory() as d:
            lib.save_json(os.path.join(d, "catalog.json"),
                          [rec(paper_id="P001", doi="10.1/x", title="A"),
                           rec(paper_id="P002", doi="10.1/x", title="B")])
            rc = dedup.main(["--run", d, "--check"])
            self.assertEqual(rc, 1)

class TestIdempotentRerun(unittest.TestCase):
    def test_second_dedup_no_id_collision(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "raw"))
            lib.save_json(os.path.join(d, "raw", "a.json"), [rec(doi="10.1/x", title="Old One")])
            dedup.update_catalog(d)
            # 第二轮：新增一篇 + 旧文件仍在（重跑场景）
            lib.save_json(os.path.join(d, "raw", "b.json"), [rec(title="New Two")])
            dedup.update_catalog(d)
            cat = lib.load_json(os.path.join(d, "catalog.json"))
            ids = [r["paper_id"] for r in cat]
            self.assertEqual(len(ids), len(set(ids)), f"paper_id 撞号: {ids}")
            self.assertEqual(sorted(ids), ["P001", "P002"])
            rc = dedup.main(["--run", d, "--check"])
            self.assertEqual(rc, 0)

    def test_id_gap_rerun_no_collision(self):
        """目录 ID 有空洞（如人工重号后 P001,P003）时，新记录不得撞已有 ID。"""
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "raw"))
            # 预置：两行，ID 为 P001 与 P003（存在空洞）
            lib.save_json(os.path.join(d, "catalog.json"),
                          [rec(paper_id="P001", doi="10.1/a", title="Row A"),
                           rec(paper_id="P003", doi="10.1/c", title="Row C")])
            lib.save_json(os.path.join(d, "raw", "b.json"), [rec(title="Brand New")])
            dedup.update_catalog(d)
            cat = lib.load_json(os.path.join(d, "catalog.json"))
            ids = sorted(r["paper_id"] for r in cat)
            self.assertEqual(ids, ["P001", "P003", "P004"])
            self.assertEqual(len(ids), len(set(ids)))

if __name__ == "__main__":
    unittest.main()
