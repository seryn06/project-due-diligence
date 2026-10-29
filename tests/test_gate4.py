import sys, pathlib, os, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tests"))
import lib, gate, gatefix

class TestG7(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = gatefix.fresh(self.tmp.name)
        self.st = gate.load_state(self.run)
    def tearDown(self):
        self.tmp.cleanup()
    def report(self):
        return os.path.join(self.run, "report.md")

    def test_g7_pass(self):
        self.assertEqual(gate.check_p7(self.run, self.st), [])

    def test_g7_1_missing_section(self):
        text = open(self.report(), encoding="utf-8").read().replace("## 7. 创新性审计", "## 7. X")
        open(self.report(), "w", encoding="utf-8").write(text)
        vs = gate.check_p7(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G7.1" for v in vs))

    def test_g7_2_ghost_citation(self):
        open(self.report(), "a", encoding="utf-8").write("\n[P999]\n")
        vs = gate.check_p7(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G7.2" for v in vs))

    def test_g7_3_no_evidence_ref(self):
        text = open(self.report(), encoding="utf-8").read().replace("(E01)", "")
        open(self.report(), "w", encoding="utf-8").write(text)
        vs = gate.check_p7(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G7.3" for v in vs))

    def test_g7_4_placeholder(self):
        open(self.report(), "a", encoding="utf-8").write("{{catalog_table}}\n")
        vs = gate.check_p7(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G7.4" for v in vs))

    def test_g7_5_undisclosed_waiver(self):
        gate.main(["waive", "--run", self.run, "G3.4", "--reason", "测试"])
        vs = gate.check_p7(self.run, gate.load_state(self.run))
        self.assertTrue(any(v["rule"] == "G7.5" for v in vs))

class TestDoi(unittest.TestCase):
    def test_doi_check_mock(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = gatefix.fresh(tmp)
            def fake_fetch(url, params=None, **kw):
                if "10.1/1" in url:
                    return {"message": {"title": ["Paper 1"]}}
                raise lib.LibError("404")
            orig = lib.fetch_json
            lib.fetch_json = fake_fetch
            try:
                # 证据引用了 P001..P005；P001 的 doi=10.1/1 可解析，
                # 其余（10.1/2..）不可解析 → check doi 应 exit 1
                rc = gate.main(["check", "doi", "--run", d])
                self.assertEqual(rc, 1)
            finally:
                lib.fetch_json = orig

    def test_doi_check_all_good_mock(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = gatefix.fresh(tmp)
            def fake_fetch(url, params=None, **kw):
                doi = url.rsplit("/", 1)[-1]
                n = doi.split("/")[-1]
                return {"message": {"title": [f"Paper {n}"]}}
            orig = lib.fetch_json
            lib.fetch_json = fake_fetch
            try:
                rc = gate.main(["check", "doi", "--run", d])
                self.assertEqual(rc, 0)
            finally:
                lib.fetch_json = orig

if __name__ == "__main__":
    unittest.main()
