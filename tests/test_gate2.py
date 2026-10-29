import sys, pathlib, os, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tests"))
import lib, gate, gatefix

class TestG3(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = gatefix.fresh(self.tmp.name)
        self.st = gate.load_state(self.run)
    def tearDown(self):
        self.tmp.cleanup()
    def cat(self):
        return lib.load_json(os.path.join(self.run, "catalog.json"))
    def save_cat(self, c):
        lib.save_json(os.path.join(self.run, "catalog.json"), c)

    def test_g3_pass(self):
        self.assertEqual(gate.check_p3(self.run, self.st), [])

    def test_g3_2_dup(self):
        c = self.cat(); c[0]["doi"] = c[1]["doi"]
        self.save_cat(c)
        vs = gate.check_p3(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G3.2" for v in vs))

    def test_g3_3_no_question(self):
        c = self.cat(); c[0]["question_ids"] = []
        self.save_cat(c)
        vs = gate.check_p3(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G3.3" for v in vs))

    def test_g3_4_quota(self):
        c = self.cat()
        for r in c:
            r["reading_status"] = "排除"; r["exclude_reason"] = "x"; r["include_reason"] = ""
        self.save_cat(c)
        vs = gate.check_p3(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G3.4" for v in vs))

    def test_g3_5_pending(self):
        c = self.cat(); c[0]["reading_status"] = "待筛"
        self.save_cat(c)
        vs = gate.check_p3(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G3.5" for v in vs))

    def test_g3_6_unexecuted(self):
        proto = lib.load_json(os.path.join(self.run, "search_protocol.json"))
        proto["queries"][0]["query"] = "ghost query"
        lib.save_json(os.path.join(self.run, "search_protocol.json"), proto)
        vs = gate.check_p3(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G3.6" for v in vs))

class TestG4(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = gatefix.fresh(self.tmp.name)
        self.st = gate.load_state(self.run)
    def tearDown(self):
        self.tmp.cleanup()

    def test_g4_pass(self):
        self.assertEqual(gate.check_p4(self.run, self.st), [])

    def test_g4_1_missing_note(self):
        os.remove(os.path.join(self.run, "paper_notes", "P001.md"))
        vs = gate.check_p4(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G4.1" for v in vs))

    def test_g4_1_missing_section(self):
        p = os.path.join(self.run, "paper_notes", "P001.md")
        text = open(p, encoding="utf-8").read().replace("## 局限", "## 缺")
        open(p, "w", encoding="utf-8").write(text)
        vs = gate.check_p4(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G4.1" for v in vs))

    def test_g4_2_l2_quota(self):
        c = lib.load_json(os.path.join(self.run, "catalog.json"))
        for r in c:
            r["reading_level"] = "L1"
        lib.save_json(os.path.join(self.run, "catalog.json"), c)
        vs = gate.check_p4(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G4.2" for v in vs))

    def test_g4_3_quote_missing(self):
        ev = lib.load_json(os.path.join(self.run, "evidence.json"))
        ev[0]["evidence_quote"] = ""
        lib.save_json(os.path.join(self.run, "evidence.json"), ev)
        vs = gate.check_p4(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G4.3" for v in vs))

if __name__ == "__main__":
    unittest.main()
