# Seedance Studio

Agent skill + toolkit: storyboard -> lint -> Seedance 2.0 prompt -> LibTV render (with dialogue / voice-over / BGM).
See `SKILL.md`. Quick start:

```
python3 scripts/sdprompt.py lint workflows/product-ad-15s.json
python3 scripts/sdprompt.py build workflows/product-ad-15s.json > p.txt
LIBTV_ACCESS_KEY=... python3 scripts/libtv_client.py send --prompt-file p.txt --wait --download out/
python3 -m unittest discover tests
```
Note: the LibTV endpoint paths in `libtv_client.py` are unverified against the live service (network to it was not available while writing); check them against libtv-labs/libtv-skills.
