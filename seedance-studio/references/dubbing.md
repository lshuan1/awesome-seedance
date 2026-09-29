# Voice / dubbing

Two modes:
1. **In-model speech (lip-sync)** — put it in the prompt: `Dialogue: (Lin, Mandarin, calm female) "..."`. Best for <=2 speakers, short lines (<= ~12 words / 4s each).
2. **Post voice-over** — generate the clip with `no dialogue`, then dub with a TTS engine and mux:
   `ffmpeg -i clip.mp4 -i vo.wav -map 0:v -map 1:a -c:v copy -shortest out.mp4`
   Use for narration, long text, or multiple languages. Write the VO script to match shot timecodes (~3 words/sec EN, ~4 chars/sec 中文).
Supplying `@audio1` as a voice reference steers timbre; keep influence ~70-80%. Only use voices you have rights to.
