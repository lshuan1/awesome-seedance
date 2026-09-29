# Failure modes -> fixes

| Symptom | Cause | Fix |
|---|---|---|
| Face/outfit drifts between shots | identity not anchored | `@image1` as character reference; repeat one fixed descriptor per shot |
| Subtitles/captions burned in | dialogue as bare prose | typed bracket + "no on-screen text" |
| Line spoken as SFX / SFX spoken | untyped audio | `Dialogue:` vs `SFX:` labels |
| Wrong accent/language | language unnamed | name language before the quote |
| Jittery or ignored camera | several moves / move late in prompt | one move, early, stable start frame |
| Warped hands, physics errors | too much action per second | fewer beats, 1 main action per shot |
| Cuts you didn't ask for | no continuity wording | "one continuous take" or explicit shot list |
| Motion copies wrong thing | reference role unstated | "@video1 for camera only" |
| Over-long prompt ignored | >~1200 chars | cut adjectives, keep constraints |

Review checklist: identity stable? camera as specified? speech audible and synced? no text/watermark? ending frame usable for chaining?
