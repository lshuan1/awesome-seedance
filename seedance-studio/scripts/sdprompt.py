#!/usr/bin/env python3
"""Seedance storyboard spec -> prompt compiler and linter (stdlib only)."""
import argparse, json, re, sys

MOVES = ["dolly-in", "dolly in", "push in", "dolly-out", "dolly out", "pull out", "pan", "tilt", "tracking",
         "follow", "orbit", "crane", "jib", "handheld", "whip pan", "dolly zoom", "fpv", "drone", "static",
         "locked-off", "one continuous take", "zoom", "推", "拉", "摇", "跟拍", "环绕", "固定"]
VAGUE = ["dynamic camera", "cinematic camera", "cool camera", "动感镜头"]
MAX_CHARS = 1200
MAX_DURATION = 15


def _fmt_t(t):
    return f"[{int(t[0]):02d}-{int(t[1]):02d}s]"


def build(spec):
    L = [f"Style: {spec['style']}. Duration: {spec['duration']}s. Aspect: {spec.get('aspect', '16:9')}."]
    for r in spec.get("references", []):
        L.append(f"@{r['tag']}: {r['role']}.")
    for i, s in enumerate(spec["shots"], 1):
        L.append(f"{_fmt_t(s['t'])} Shot {i}: {s['size']}, {s['move']}, {s['subject']} {s['action']}"
                 + (f", {s['setting']}" if s.get("setting") else "") + ".")
        d = s.get("dialogue")
        if d:
            L.append(f"  Dialogue: ({d['speaker']}, {d['lang']}) \"{d['text']}\"")
        v = s.get("voiceover")
        if v:
            L.append(f"  Voice-over: ({v['lang']}) \"{v['text']}\"")
        if s.get("sfx"):
            L.append(f"  SFX: {s['sfx']}")
    if spec.get("bgm"):
        L.append(f"BGM: {spec['bgm']}.")
    if spec.get("constraints"):
        L.append("Constraints: " + "; ".join(spec["constraints"]) + ".")
    return "\n".join(L)


def lint(spec):
    out = []
    err = lambda m: out.append(("ERROR", m))
    warn = lambda m: out.append(("WARN", m))
    for k in ("style", "duration", "shots"):
        if k not in spec:
            err(f"missing field '{k}'")
    if out:
        return out
    dur = spec["duration"]
    if dur > MAX_DURATION:
        err(f"duration {dur}s > {MAX_DURATION}s: split into chained clips")
    shots = spec["shots"]
    if not 1 <= len(shots) <= 5:
        warn(f"{len(shots)} shots; 1-5 recommended per clip")
    prev_end = 0
    tags = {r["tag"] for r in spec.get("references", [])}
    counts = {"image": 0, "video": 0, "audio": 0}
    for t in tags:
        for k in counts:
            if t.startswith(k):
                counts[k] += 1
    if counts["image"] > 9 or counts["video"] > 3 or counts["audio"] > 3 or sum(counts.values()) > 12:
        err(f"too many references {counts}")
    used = set()
    for i, s in enumerate(shots, 1):
        p = f"shot {i}"
        for k in ("t", "size", "move", "subject", "action"):
            if k not in s:
                err(f"{p}: missing '{k}'")
        if "t" not in s:
            continue
        a, b = s["t"]
        if a != prev_end:
            err(f"{p}: starts at {a}s but previous ended at {prev_end}s (gap/overlap)")
        if b - a < 2:
            warn(f"{p}: under 2s is too short to render reliably")
        prev_end = b
        mv = s.get("move", "").lower()
        if any(v in mv for v in VAGUE) or not any(m in mv for m in MOVES):
            err(f"{p}: camera move '{s.get('move')}' is vague/unknown; see references/camera-moves.md")
        if len(re.split(r"\b(?:and|then|with)\b|,|\+|，", mv)) > 1 and sum(m in mv for m in MOVES) > 1:
            warn(f"{p}: multiple camera moves stacked; use one per shot")
        d = s.get("dialogue")
        if d:
            for k in ("speaker", "lang", "text"):
                if not d.get(k):
                    err(f"{p}: dialogue missing '{k}' (language must be named)")
            words = len(d.get("text", "").split()) if " " in d.get("text", "") else len(d.get("text", "")) / 4
            if words > 3 * max(b - a, 1) + 1:
                warn(f"{p}: dialogue too long for {b-a}s window")
        text = " ".join(str(s.get(k, "")) for k in ("subject", "action", "setting"))
        used |= set(re.findall(r"@([a-z]+\d+)", text))
    if prev_end != dur:
        err(f"shots end at {prev_end}s but duration is {dur}s")
    for u in used - tags:
        err(f"@{u} used but not declared in references")
    for t in sorted(tags - used):
        warn(f"reference @{t} declared but never used in a shot")
    if "no on-screen text" not in " ".join(spec.get("constraints", [])).lower():
        warn("add constraint 'no on-screen text' to avoid burned-in captions")
    n = len(build(spec)) if not out or all(l != "ERROR" for l, _ in out) else 0
    if n > MAX_CHARS:
        warn(f"prompt is {n} chars (> {MAX_CHARS}); trim")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["lint", "build"])
    ap.add_argument("spec")
    a = ap.parse_args(argv)
    spec = json.load(open(a.spec, encoding="utf-8"))
    if a.cmd == "build":
        print(build(spec))
        return 0
    res = lint(spec)
    for lvl, m in res:
        print(f"{lvl}: {m}")
    if not res:
        print("OK")
    return 1 if any(l == "ERROR" for l, _ in res) else 0


if __name__ == "__main__":
    sys.exit(main())
