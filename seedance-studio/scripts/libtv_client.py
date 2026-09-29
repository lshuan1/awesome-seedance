#!/usr/bin/env python3
"""Minimal LibTV client. Endpoints mirror libtv-labs/libtv-skills scripts; verify paths against that repo
if the service changes. Auth: LIBTV_ACCESS_KEY (Bearer). Base: IM_BASE_URL (default https://im.liblib.tv)."""
import argparse, json, os, sys, time, urllib.request

BASE = os.environ.get("IM_BASE_URL") or os.environ.get("OPENAPI_IM_BASE") or "https://im.liblib.tv"
URL_RE = __import__("re").compile(r"https?://[^\s\"'<>)]+\.(?:mp4|mov|png|jpg|jpeg|webp)", 2)


def _req(path, body=None, method=None):
    key = os.environ.get("LIBTV_ACCESS_KEY")
    if not key:
        sys.exit("LIBTV_ACCESS_KEY is not set")
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method or ("POST" if data else "GET"),
                               headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=60) as f:
        return json.load(f)


def extract_urls(messages):
    seen, out = set(), []
    for m in messages:
        if m.get("role") != "assistant":
            continue
        for u in URL_RE.findall(json.dumps(m.get("content", ""), ensure_ascii=False)):
            if u not in seen:
                seen.add(u); out.append(u)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("send"); s.add_argument("--prompt-file", required=True)
    s.add_argument("--session"); s.add_argument("--wait", action="store_true")
    s.add_argument("--download"); s.add_argument("--timeout", type=int, default=900)
    q = sub.add_parser("query"); q.add_argument("session")
    a = ap.parse_args(argv)
    if a.cmd == "query":
        print(json.dumps(_req(f"/openapi/session/{a.session}"), ensure_ascii=False, indent=1)); return
    prompt = open(a.prompt_file, encoding="utf-8").read()
    body = {"message": prompt}
    if a.session:
        body["sessionId"] = a.session
    r = _req("/openapi/session", body)
    sid = r.get("sessionId") or (r.get("data") or {}).get("sessionId")
    print("session:", sid, r.get("projectUrl", ""))
    if not a.wait:
        return
    deadline = time.time() + a.timeout
    while time.time() < deadline:
        time.sleep(8)
        res = _req(f"/openapi/session/{sid}")
        msgs = res.get("messages") or res.get("data") or []
        urls = extract_urls(msgs)
        if urls:
            for u in urls:
                print(u)
                if a.download:
                    os.makedirs(a.download, exist_ok=True)
                    urllib.request.urlretrieve(u, os.path.join(a.download, u.split("/")[-1]))
            return
    sys.exit("timed out waiting for results")


if __name__ == "__main__":
    main()
