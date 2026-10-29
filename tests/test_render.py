import sys, pathlib, os, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tests"))
import lib, gate, gatefix, render_report as rr

class TestTables(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = gatefix.fresh(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()

    def test_catalog_table_included_only(self):
        t = rr.table_catalog(self.run)
        self.assertIn("P001", t)
        self.assertNotIn("Excluded 1", t)

    def test_gap_table(self):
        t = rr.table_gaps(self.run)
        self.assertIn("G-01", t)

    def test_search_stats(self):
        t = rr.table_search_stats(self.run)
        self.assertIn("openalex", t)
        self.assertIn("反证", t)

class TestBuild(unittest.TestCase):
    def test_build_fills_tokens_and_passes_g7(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = gatefix.fresh(tmp)
            tpl = os.path.join(tmp, "tpl.md")
            fs = "深度下限填充正文样例。" * 12
            fl = "深度下限填充正文样例，长章节需要更长的分析正文。" * 12
            open(tpl, "w", encoding="utf-8").write(
                f"# {{{{project_name}}}} {{{{generated_at}}}}\n\n## 1. Executive Summary\n\n见 (E01)。{fs}\n"
                f"## 2. 项目分解\nx\n## 3. 文献检索协议（含覆盖限制）\nx\n## 4. 研究现状\n{fl}\n"
                f"## 5. 痛点分析\n{fs}\n## 6. 研究缺口台账\n\n{{{{gap_table}}}}\n## 7. 创新性审计\nx\n"
                f"## 8. 候选研究方向\n{fl}\n## 9. 可行性与风险\n{fs}\n## 10. 推荐路线图\n{fs}\n"
                f"## 11. 证据附录\n\n{{{{catalog_table}}}}\n\n{{{{search_stats}}}}\n\n统计：{{{{evidence_count}}}}\n"
                f"{{{{waiver_table}}}}\n")
            out = os.path.join(tmp, "report.md")
            rr.build_report(run, template=tpl, out=out)
            text = open(out, encoding="utf-8").read()
            self.assertNotIn("{{", text)
            self.assertIn("G-01", text)
            self.assertIn("P001", text)
            st = gate.load_state(run)
            self.assertEqual(gate.check_p7(run, st), [])

if __name__ == "__main__":
    unittest.main()
