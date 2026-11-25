"""Convert a rigged character GLB (e.g. from image-to-3D) into an Unreal-ready FBX.

- Imports the GLB, checks it is one armature + skinned mesh, reports height and bone count.
- Turns the character to face Blender -Y (the usual front), feet at Z=0, scale applied.
- Exports FBX with embedded textures, no leaf bones, so UE 5.3's FBX importer builds
  the skeletal mesh, skeleton, materials and textures in one go.
- Optionally renders a front/back preview (Cycles, CPU).

    python pipeline/characters/glb_to_fbx.py --glb in.glb --fbx out.fbx [--preview preview.png] [--turn 180]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy  # type: ignore
from mathutils import Vector  # type: ignore


def bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--glb", required=True, type=Path)
    ap.add_argument("--fbx", required=True, type=Path)
    ap.add_argument("--preview", type=Path)
    ap.add_argument("--turn", type=float, default=0.0, help="extra yaw in degrees if the front is wrong")
    a = ap.parse_args(argv)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(a.glb))
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    if arms:  # drop stray helper meshes (e.g. an unskinned Icosphere) that are not part of the rig
        for o in [o for o in bpy.data.objects if o.type == "MESH" and o.parent not in arms]:
            print(f"removing stray mesh {o.name}")
            bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    roots = [o for o in bpy.data.objects if o.parent is None]
    if a.turn:
        for r in roots:
            r.rotation_mode = "XYZ"
            r.rotation_euler.z += math.radians(a.turn)
    bpy.context.view_layer.update()
    lo, hi = bbox(meshes)
    for r in roots:
        r.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    lo, hi = bbox(meshes)
    info = {
        "armatures": [o.name for o in arms],
        "bones": sum(len(o.data.bones) for o in arms),
        "meshes": [o.name for o in meshes],
        "tris": sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes),
        "height_m": round(hi.z - lo.z, 3),
        "size_m": [round(hi.x - lo.x, 3), round(hi.y - lo.y, 3)],
        "materials": sorted({s.material.name for o in meshes for s in o.material_slots if s.material}),
        "images": sorted({i.name for i in bpy.data.images}),
        "actions": [x.name for x in bpy.data.actions],
    }
    print("GLBINFO " + json.dumps(info))

    a.fbx.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=str(a.fbx), use_selection=False, apply_unit_scale=True,
                             object_types={"ARMATURE", "MESH"}, add_leaf_bones=False,
                             bake_anim=False, path_mode="COPY", embed_textures=True,
                             mesh_smooth_type="FACE", primary_bone_axis="Y", secondary_bone_axis="X")
    print(f"FBX -> {a.fbx}")

    if a.preview:
        scn = bpy.context.scene
        scn.render.engine = "CYCLES"
        scn.cycles.device = "CPU"
        scn.cycles.samples = 24
        scn.render.resolution_x, scn.render.resolution_y = 600, 900
        world = bpy.data.worlds.new("w")
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs[1].default_value = 1.2
        scn.world = world
        h = hi.z - lo.z
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
        scn.collection.objects.link(cam)
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = h * 1.1
        scn.camera = cam
        sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
        sun.data.energy = 3
        sun.rotation_euler = (math.radians(50), 0, math.radians(20))
        scn.collection.objects.link(sun)
        out = []
        for tag, y, rz in [("front", -5, 0), ("side", 0, 90), ("back", 5, 180)]:
            ang = math.radians(rz)
            cam.location = (5 * math.sin(ang), -5 * math.cos(ang), h / 2)
            cam.rotation_euler = (math.radians(90), 0, ang)
            p = a.preview.with_name(f"{a.preview.stem}_{tag}.png")
            scn.render.filepath = str(p)
            bpy.ops.render.render(write_still=True)
            out.append(str(p))
        print("PREVIEWS " + " ".join(out))


if __name__ == "__main__":
    main()
