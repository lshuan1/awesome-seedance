import copy, json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import sdprompt, libtv_client
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
