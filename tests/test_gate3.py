import sys, pathlib, os, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tests"))
import lib, gate, gatefix

class TestG5(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = gatefix.fresh(self.tmp.name)
        self.st = gate.load_state(self.run)
    def tearDown(self):
        self.tmp.cleanup()
    def gaps(self):
        return lib.load_json(os.path.join(self.run, "gaps.json"))
    def save_gaps(self, g):
        lib.save_json(os.path.join(self.run, "gaps.json"), g)

    def test_g5_pass(self):
        self.assertEqual(gate.check_p5(self.run, self.st), [])

    def test_g5_1_count(self):
        g = self.gaps(); self.save_gaps(g[:1])
        vs = gate.check_p5(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G5.1" for v in vs))

    def test_g5_2_unresolvable(self):
        g = self.gaps(); g[0]["supporting_evidence"] = ["E99"]
        self.save_gaps(g)
        vs = gate.check_p5(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G5.2" for v in vs))

    def test_g5_3_confirmed_without_counter(self):
        # fixture 的反证查询挂在每个 Q{i} 上；把已确认缺口挪到无反证的问题即可触发
        g = self.gaps()
        all_q = {q for q, _, _ in gate.parse_tree(self.run) if q.startswith("Q")}
        counter_q = {q for q in all_q if any(
            e.get("path") == "反证" and e.get("question_id") == q
            for e in lib.load_json(os.path.join(self.run, "search_log.json")))}
        g[0]["question_id"] = sorted(all_q - counter_q)[0]
        self.save_gaps(g)
        vs = gate.check_p5(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G5.3" for v in vs))

    def test_g5_3_confirmed_single_source(self):
        g = self.gaps(); g[0]["supporting_evidence"] = ["E01"]
        self.save_gaps(g)
        vs = gate.check_p5(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G5.3" for v in vs))

    def test_g5_4_empty_field(self):
        g = self.gaps(); g[1]["validation_plan"] = ""
        self.save_gaps(g)
        vs = gate.check_p5(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G5.4" for v in vs))

class TestG6(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = gatefix.fresh(self.tmp.name)
        self.st = gate.load_state(self.run)
    def tearDown(self):
        self.tmp.cleanup()
    def na(self):
        return lib.load_json(os.path.join(self.run, "novelty_audit.json"))
    def save_na(self, x):
        lib.save_json(os.path.join(self.run, "novelty_audit.json"), x)

    def test_g6_pass(self):
        self.assertEqual(gate.check_p6(self.run, self.st), [])

    def test_g6_1_empty(self):
        self.save_na({"directions": []})
        vs = gate.check_p6(self.run, self.st)
        self.assertEqual(vs[0]["rule"], "G6.1")

    def test_g6_2_no_prior_query(self):
        x = self.na(); x["directions"][0]["closest_prior_queries"] = []
        self.save_na(x)
        vs = gate.check_p6(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G6.2" for v in vs))

    def test_g6_2_wrong_path(self):
        x = self.na(); x["directions"][0]["closest_prior_queries"] = ["SP01"]  # 综述线
        self.save_na(x)
        vs = gate.check_p6(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G6.2" for v in vs))

    def test_g6_3_bad_bucket(self):
        x = self.na(); x["directions"][0]["subclaims"][0]["bucket"] = "很创新"
        self.save_na(x)
        vs = gate.check_p6(self.run, self.st)
        self.assertTrue(any(v["rule"] == "G6.3" for v in vs))

if __name__ == "__main__":
    unittest.main()
