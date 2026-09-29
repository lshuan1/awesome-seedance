import copy, json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import sdprompt, libtv_client, blockout
W = os.path.join(os.path.dirname(__file__), "..", "workflows")
load = lambda n: json.load(open(os.path.join(W, n), encoding="utf-8"))


class T(unittest.TestCase):
    def test_templates_have_no_errors(self):
        for n in os.listdir(W):
            self.assertFalse([m for l, m in sdprompt.lint(load(n)) if l == "ERROR"], n)

    def test_gap_and_vague_move(self):
        s = load("product-ad-15s.json")
        s["shots"][1]["t"] = [6, 10]
        s["shots"][0]["move"] = "dynamic camera"
        msgs = [m for _, m in sdprompt.lint(s)]
        self.assertTrue(any("gap" in m for m in msgs))
        self.assertTrue(any("vague" in m for m in msgs))

    def test_undeclared_ref_and_duration(self):
        s = load("product-ad-15s.json")
        s["references"] = []
        s["duration"] = 20
        msgs = [m for _, m in sdprompt.lint(s)]
        self.assertTrue(any("not declared" in m for m in msgs))
        self.assertTrue(any("split" in m for m in msgs))

    def test_build_contains_typed_audio(self):
        p = sdprompt.build(load("long-film-chain.json"))
        self.assertIn('Dialogue: (Lin, Mandarin) "我到了。"', p)
        self.assertIn("SFX:", p)

    def test_extract_urls(self):
        m = [{"role": "assistant", "content": "done https://x.io/a.mp4 ok"}, {"role": "user", "content": "https://x.io/b.mp4"}]
        self.assertEqual(libtv_client.extract_urls(m), ["https://x.io/a.mp4"])


if __name__ == "__main__":
    unittest.main()


class B(unittest.TestCase):
    def setUp(self):
        import blockout
        self.b = blockout
        self.scene = json.load(open(os.path.join(W, "..", "scenes", "scene-station.json"), encoding="utf-8"))

    def test_infer_moves(self):
        cam = lambda a, la_a, b, la_b: {"keys": [{"t": 0, "pos": a, "look_at": la_a}, {"t": 5, "pos": b, "look_at": la_b}]}
        self.assertIn("dolly-in", self.b.infer_move(cam([0, -8, 1], [0, 0, 1], [0, -3, 1], [0, 0, 1])))
        self.assertIn("dolly-out", self.b.infer_move(cam([0, -3, 1], [0, 0, 1], [0, -8, 1], [0, 0, 1])))
        self.assertIn("orbit", self.b.infer_move(cam([5, 0, 1], [0, 0, 1], [0, 5, 1], [0, 0, 1])))
        self.assertIn("crane up", self.b.infer_move(cam([0, -5, 1], [0, 0, 1], [0, -5, 5], [0, 0, 1])))
        self.assertIn("static", self.b.infer_move(cam([0, -5, 1], [0, 0, 1], [0, -5, 1], [0, 0, 1])))

    def test_svg_and_bpy_script_compile(self):
        self.assertIn("<svg", self.b.svg(self.scene))
        compile(self.b.blender_script(self.scene, "/tmp/x"), "bpy_script", "exec")

    def test_import_package(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            for n in ("shot_reference.mp4", "shot_depth.mp4", "shot.json"):
                open(os.path.join(d, n), "w").close()
            r = self.b.import_package(d)
        self.assertEqual([x["tag"] for x in r["references"]], ["video1", "video2"])
