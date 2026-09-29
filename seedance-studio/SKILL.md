---
name: seedance-studio
description: Plan, write, lint and render Seedance 2.0 videos (with camera moves, dialogue/voice-over and BGM) through LibTV or any Seedance API. Use when the user wants a high-success-rate AI video from an idea, script or reference files.
---

# Seedance Studio

A director layer in front of LibTV / Seedance 2.0. Unlike the plain LibTV skill
(a "courier" that forwards text unchanged), this skill first turns the idea into a
**structured storyboard**, compiles it into a Seedance-optimised prompt, **lints** it
against known failure modes, and only then submits it.

## Workflow

1. **Brief** – Ask only for what is missing: subject, duration (<=15s per clip), aspect ratio, language of speech, reference files.
2. **Storyboard** – Write a spec JSON (`workflows/*.json` are templates). One shot = one camera move. See `references/prompt-formula.md`.
3. **Lint** – `python3 scripts/sdprompt.py lint spec.json` — fix every `ERROR`, consider every `WARN`.
4. **Compile** – `python3 scripts/sdprompt.py build spec.json` prints the final prompt.
5. **Render** – `python3 scripts/libtv_client.py send --prompt-file p.txt --wait --download out/`
   (needs `LIBTV_ACCESS_KEY`; base URL override via `IM_BASE_URL`). Upload references first with `upload`.
6. **Review & continue** – Judge the clip against the checklist in `references/failure-modes.md`; for long films chain clips using the last frame as `@image1` for the next (see `workflows/long-film-chain.json`).

## Rules that raise success rate

- Shortest prompt that unambiguously fixes subject, action, camera, environment, sound, continuity.
- Every reference gets an explicit role (`@image1` = identity, `@video1` = camera only, `@audio1` = rhythm).
- One named camera move per shot, stated early, with a stable starting composition.
- Speech goes in typed brackets with the language named; never leave dialogue as bare prose.
- Voice-over is separate from lip-sync dialogue: see `references/dubbing.md`.
- Never fabricate real people's likeness or voices without consent.
