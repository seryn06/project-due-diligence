import sys, pathlib, os, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tests"))
import lib, gate, gatefix

class TestG1G2(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = gatefix.fresh(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()

    def test_g1_pass(self):
        self.assertEqual(gate.check_p1(self.run, gate.load_state(self.run)), [])

    def test_g1_fail_core_count(self):
        p = os.path.join(self.run, "question_tree.md")
        open(p, "w", encoding="utf-8").write("- Q1 a — 理由：x\n")
        vs = gate.check_p1(self.run, gate.load_state(self.run))
        self.assertTrue(any(v["rule"] == "G1.1" for v in vs))

    def test_g1_fail_no_reason(self):
        p = os.path.join(self.run, "question_tree.md")
        open(p, "w", encoding="utf-8").write(
            "\n".join(f"- Q{i} 核心问题{i}" for i in range(1, 6)))
        vs = gate.check_p1(self.run, gate.load_state(self.run))
        self.assertTrue(any(v["rule"] == "G1.2" for v in vs))

    def test_g2_pass_and_fail_cell(self):
        st = gate.load_state(self.run)
        self.assertEqual(gate.check_p2(self.run, st), [])
        proto = lib.load_json(os.path.join(self.run, "search_protocol.json"))
        proto["queries"] = [q for q in proto["queries"] if q["path"] != "反证"]
        lib.save_json(os.path.join(self.run, "search_protocol.json"), proto)
        vs = gate.check_p2(self.run, st)
        self.assertTrue(any(v["rule"] == "G2.1" for v in vs))

class TestStateMachine(unittest.TestCase):
    def test_new_set_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, "r2")
            gate.main(["new", "--run", d, "--tier", "快速", "--project", "t"])
            st = lib.load_json(os.path.join(d, "state.json"))
            self.assertEqual((st["phase"], st["tier"]), ("P1", "快速"))
            gatefix.full_run(d, "快速", with_state=False)   # 覆盖产物，保留 state
            rc = gate.main(["set-phase", "--run", d, "P2"])
            self.assertEqual(rc, 0)
            st = lib.load_json(os.path.join(d, "state.json"))
            self.assertEqual(st["phase"], "P2")
            self.assertTrue(st["gate_results"]["P1"]["passed"])

    def test_check_exit_code_and_waive(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = gatefix.fresh(tmp, "r3")
            p = os.path.join(d, "question_tree.md")
            open(p, "w", encoding="utf-8").write("- Q1 x — 理由：y\n")  # 破坏 G1.1
            rc = gate.main(["check", "P1", "--run", d])
            self.assertEqual(rc, 1)
            gate.main(["waive", "--run", d, "G1.1", "--reason", "测试豁免"])
            rc = gate.main(["check", "P1", "--run", d])
            self.assertEqual(rc, 0)
            st = lib.load_json(os.path.join(d, "state.json"))
            self.assertEqual(st["waivers"][0]["rule"], "G1.1")

    def test_set_phase_refuses_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, "r4")
            gate.main(["new", "--run", d, "--tier", "快速", "--project", "t"])
            gatefix.full_run(d, "快速", with_state=False)
            with self.assertRaises(SystemExit):
                gate.main(["set-phase", "--run", d, "P4"])

    def test_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = gatefix.fresh(tmp, "r5")
            rc = gate.main(["status", "--run", d])
            self.assertEqual(rc, 0)

if __name__ == "__main__":
    unittest.main()
