# 3D blockout -> Seedance (for complex scenes)

Why: text alone cannot pin down layout, scale, or a precise camera path. A grey-box render gives Seedance a
`@video` for camera + blocking, and a depth pass for layout, so the prompt only has to describe look and performance.

## Pipeline
1. **Stage** the scene in boxes (one box per major object, mannequin = tall box). Any of:
   - `scripts/blockout.py blender scene.json build.py` then `blender -b -P build.py` (headless, clay + depth mp4). *Untested against a live Blender in this repo.*
   - [wassermanproductions/blockout](https://github.com/wassermanproductions/blockout) (Apache-2.0, Electron, has a 33-tool MCP server so Claude can stage scenes; exports reference video, depth, stills, prompt, metadata JSON). Read its NOTICE for the attribution requirement.
   - [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) (MIT) to let Claude drive full Blender, including `execute_blender_code`. Review generated code before running.
   - Calliope (benjiyaya/Calliope) three.js "Build Scene" blockout, if you want an all-in-one UI.
2. **Name the move**: `scripts/blockout.py infer scene.json` -> paste into the shot's `move`.
3. **Preview layout**: `scripts/blockout.py svg scene.json plan.svg`.
4. **Upload** clay/reference video (`@video1`) and optional depth (`@video2`); declare roles in the spec:
   - `@video1`: "camera movement and blocking only; do not copy grey textures or mannequin look"
   - `@image1`: identity/look frames for the real characters and set
5. Lint, build, render as usual. If the result copies the grey look, restate the role and add a styled first frame as `@image`.

## Caveats
- Seedance takes video references as loose guidance, not strict ControlNet depth conditioning; for hard depth control use an open model (Wan/LTX via ComfyUI, which Blockout pre-wires).
- Reference-file count limits still apply (see prompt-formula.md); a depth video costs one of your 3 video slots.
- Blockout package file names are matched heuristically by `blockout.py import`; verify against your export.
