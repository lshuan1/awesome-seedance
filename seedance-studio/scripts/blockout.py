#!/usr/bin/env python3
"""3D grey-box blockout helper (stdlib only).

  infer   scene.json      -> camera move wording inferred from camera keyframes
  svg     scene.json out  -> top-down blocking diagram (no Blender needed)
  blender scene.json out  -> bpy script that builds boxes, keys the camera and
                             renders clay + depth videos (run: blender -b -P out.py)
  import  package_dir     -> read a Blockout (wassermanproductions/blockout) export
                             package and print the reference block for a spec

Scene JSON: {"objects":[{"name","size":[w,d,h],"pos":[x,y,z],"path":[{"t","pos"}]}],
             "camera":{"lens_mm":35,"keys":[{"t","pos":[x,y,z],"look_at":[x,y,z]}]}}
Z is up, metres.
"""
import json, math, os, sys


def _sub(a, b): return [x - y for x, y in zip(a, b)]
def _len(a): return math.sqrt(sum(x * x for x in a))


def infer_move(cam):
    """Name the dominant camera move from first/last keyframe. Thresholds are heuristic."""
    k = cam["keys"]
    if len(k) < 2:
        return "locked-off static camera"
    a, b = k[0], k[-1]
    move = _sub(b["pos"], a["pos"])
    d0, d1 = _len(_sub(a["look_at"], a["pos"])), _len(_sub(b["look_at"], b["pos"]))
    look_shift = _len(_sub(b["look_at"], a["look_at"]))
    ang0 = math.atan2(a["pos"][1] - a["look_at"][1], a["pos"][0] - a["look_at"][0])
    ang1 = math.atan2(b["pos"][1] - b["look_at"][1], b["pos"][0] - b["look_at"][0])
    dang = abs(math.degrees((ang1 - ang0 + math.pi) % (2 * math.pi) - math.pi))
    if dang > 45 and abs(d1 - d0) < 0.25 * max(d0, 1e-6):
        return f"{int(round(dang))}-degree orbit around the subject"
    if _len(move) < 0.2:
        return "smooth pan" if look_shift > 0.3 else "locked-off static camera"
    if abs(move[2]) > 0.6 * _len(move):
        return "crane up" if move[2] > 0 else "crane down"
    if abs(d1 - d0) > 0.35 * max(d0, 1e-6):
        return "slow dolly-in" if d1 < d0 else "dolly-out"
    return "tracking shot following alongside the subject"


def svg(scene):
    objs = scene["objects"]
    pts = [o["pos"][:2] for o in objs] + [k["pos"][:2] for k in scene["camera"]["keys"]]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0, s = min(xs) - 2, min(ys) - 2, 40
    W, H = (max(xs) + 2 - x0) * s, (max(ys) + 2 - y0) * s
    P = lambda x, y: ((x - x0) * s, H - (y - y0) * s)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" style="background:#fff">']
    for o in objs:
        w, d = o["size"][0], o["size"][1]
        px, py = P(o["pos"][0] - w / 2, o["pos"][1] + d / 2)
        out.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{w*s:.1f}" height="{d*s:.1f}" fill="#ccc" stroke="#333"/>')
        out.append(f'<text x="{px:.1f}" y="{py-3:.1f}" font-size="11">{o["name"]}</text>')
    path = " ".join("%.1f,%.1f" % P(*k["pos"][:2]) for k in scene["camera"]["keys"])
    out.append(f'<polyline points="{path}" fill="none" stroke="#d33" stroke-width="2" stroke-dasharray="5"/>')
    out.append(f'<text x="6" y="14" font-size="11" fill="#d33">camera: {infer_move(scene["camera"])}</text></svg>')
    return "\n".join(out)


BPY = '''import bpy, math
from mathutils import Vector
S = %s
FPS = %d
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.render.resolution_x, sc.render.resolution_y = %d, %d
sc.render.engine = "BLENDER_WORKBENCH"
clay = bpy.data.materials.new("clay"); clay.diffuse_color = (0.6, 0.6, 0.6, 1)
objs = {}
for o in S["objects"]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=o["pos"])
    b = bpy.context.active_object; b.name = o["name"]
    b.scale = o["size"]; b.location[2] = o["pos"][2] + o["size"][2] / 2
    b.data.materials.append(clay); objs[o["name"]] = b
    for k in o.get("path", []):
        b.location = (k["pos"][0], k["pos"][1], k["pos"][2] + o["size"][2] / 2)
        b.keyframe_insert("location", frame=int(k["t"] * FPS) + 1)
cd = bpy.data.cameras.new("cam"); cd.lens = S["camera"].get("lens_mm", 35)
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
for k in S["camera"]["keys"]:
    cam.location = k["pos"]
    d = Vector(k["look_at"]) - Vector(k["pos"])
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    f = int(k["t"] * FPS) + 1
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
sc.frame_start, sc.frame_end = 1, int(S["camera"]["keys"][-1]["t"] * FPS) + 1
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.rotation_euler = (0.9, 0.2, 0.6)
OUT = %r
def render(path, depth):
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"; sc.render.ffmpeg.codec = "H264"
    sc.render.filepath = path
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    bpy.ops.render.render(animation=True)
render(OUT + "/clay.mp4", False)
# Depth pass: Workbench has no Z output, so re-render with a mist-style white->black falloff via compositor
sc.use_nodes = True; sc.view_layers[0].use_pass_z = True
nt = sc.node_tree; nt.nodes.clear()
rl = nt.nodes.new("CompositorNodeRLayers"); nm = nt.nodes.new("CompositorNodeNormalize")
inv = nt.nodes.new("CompositorNodeInvert"); cmp = nt.nodes.new("CompositorNodeComposite")
nt.links.new(rl.outputs["Depth"], nm.inputs[0]); nt.links.new(nm.outputs[0], inv.inputs["Color"])
nt.links.new(inv.outputs[0], cmp.inputs["Image"])
sc.render.engine = "BLENDER_EEVEE_NEXT" if hasattr(bpy.types, "SCENE_PT_eevee_next") else "BLENDER_EEVEE"
render(OUT + "/depth.mp4", True)
'''


def blender_script(scene, out_dir, fps=24, res=(1280, 720)):
    return BPY % (json.dumps(scene), fps, res[0], res[1], out_dir)


def import_package(d):
    """Map a Blockout export package to spec references. File names are matched by pattern since the
    package layout may change between Blockout versions."""
    files = sorted(os.listdir(d))
    pick = lambda *keys: next((f for f in files if all(k in f.lower() for k in keys)), None)
    ref = pick("reference", ".mp4") or pick("ref", ".mp4")
    depth = pick("depth", ".mp4")
    refs = []
    if ref:
        refs.append({"tag": "video1", "file": ref, "role": "camera movement and blocking only; do not copy grey textures"})
    if depth:
        refs.append({"tag": "video2", "file": depth, "role": "depth/layout guide only"})
    meta = pick(".json")
    return {"references": refs, "metadata": meta}


def main(argv=None):
    a = argv or sys.argv[1:]
    if len(a) < 2 or a[0] not in ("infer", "svg", "blender", "import"):
        sys.exit(__doc__)
    if a[0] == "import":
        print(json.dumps(import_package(a[1]), indent=1, ensure_ascii=False)); return
    scene = json.load(open(a[1], encoding="utf-8"))
    if a[0] == "infer":
        print(infer_move(scene["camera"]))
    elif a[0] == "svg":
        open(a[2], "w").write(svg(scene))
    else:
        open(a[2], "w").write(blender_script(scene, os.path.abspath(os.path.dirname(a[2]) or ".")))


if __name__ == "__main__":
    main()
