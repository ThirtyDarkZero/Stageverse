"""Prepare Stadium_Main from the purchased stadium OBJ (sofi-stadium.zip in project files).

What it does:
  1. Imports the OBJ (Y up) into Blender (Z up).
  2. De-brands it: deletes the roof logo object and replaces the 'screen' texture
     (real-venue branding) with a plain dark material. No real venue name ships.
  3. Moves the playing field centre to the origin at Z = 0 and turns the field's long
     axis onto X, so the venue matches the StageVerse frame (stage at -X).
  4. Exports one FBX per part to unreal/SourceArt/Venues/Stadium_Main/ and writes
     markers.json with the stage zone, performer marks, FOH and field zones.

DO NOT COMMIT THE FBX OUTPUT until Rob has confirmed the model's licence allows use in a
distributed game (see docs/venues/stadium_main.md). markers.json is ours and can be committed.

Run with the bpy wheel (Python 3.11):
    python pipeline/venues/stadium_prep.py --obj "/path/Sofi stadium.obj" [--out unreal/SourceArt/Venues/Stadium_Main]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import bpy  # type: ignore
from mathutils import Matrix, Vector  # type: ignore

VENUE = "Stadium_Main"
FIELD_OBJECT = "Sofi_stadium"          # playing surface in the source file
BRANDING_OBJECTS = ["Sofi_stadium_Logo"]  # removed outright
BRANDING_TEXTURES = ["screen"]          # image names (no extension) swapped for a plain material

# Source object -> exported part name (neutral names only)
PARTS = {
    "Sofi_stadium": "Field",
    "Sofi_stadium_Target": "FieldMarkings",
    "Sofi_stadium_Land_Scabe_IN": "FieldSurround",
    "sofi_stadium_Chairs": "Seats",
    "sofi_stadium_Buldding": "Bowl",
    "Sofi_stadium_Frame": "BowlFrame",
    "Sofi_stadium_Interior_Glass": "InteriorGlass",
    "Sofi_stadium_Interior__Structure": "InteriorStructure",
    "Sofi_stadium_TV_Smart": "CenterBoard",
    "Sofi_stadium_Main_Structure": "Canopy",
    "Sofi_stadium_Main_Body": "CanopyBody",
    "Sofi_stadium_Frame_Body": "CanopyFrame",
    "Sofi_stadium_Glass_Body": "CanopyGlass",
    "Sofi_stadium_Glass_2": "Glass2",
    "Sofi_stadium_Land_Scabe": "Landscape",
    "Sofi_stadium_Land_Scabe_F": "LandscapeFeatures",
    "sofi_stadium_Ground": "Ground",
}

STAGE_UPSTAGE_X = -72.0  # end stage sits past the -X end line (field half-length ~55 m)


def import_obj(path: Path) -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=str(path), forward_axis="NEGATIVE_Z", up_axis="Y")


def debrand() -> list[str]:
    removed = []
    for name in BRANDING_OBJECTS:
        ob = bpy.data.objects.get(name)
        if ob:
            bpy.data.objects.remove(ob, do_unlink=True)
            removed.append(name)
    plain = bpy.data.materials.new("M_Stadium_Screen_Blank")
    plain.diffuse_color = (0.02, 0.02, 0.02, 1)
    for mat in list(bpy.data.materials):
        if not mat.use_nodes:
            continue
        for node in mat.node_tree.nodes:
            img = getattr(node, "image", None)
            if img and Path(img.filepath).stem.lower() in BRANDING_TEXTURES:
                for ob in bpy.data.objects:
                    for slot in ob.material_slots:
                        if slot.material == mat:
                            slot.material = plain
                removed.append(f"texture:{img.name}")
                break
    return removed


def world_bbox(ob) -> tuple[Vector, Vector]:
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


def normalise_frame() -> dict:
    field = bpy.data.objects[FIELD_OBJECT]
    lo, hi = world_bbox(field)
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z))
    size = hi - lo
    rot = Matrix.Identity(4)
    if size.y > size.x:  # long axis on Y: turn it onto X
        rot = Matrix.Rotation(math.radians(90), 4, "Z")
    xf = rot @ Matrix.Translation(-centre)
    for ob in bpy.data.objects:
        if ob.parent is None:
            ob.matrix_world = xf @ ob.matrix_world
    lo, hi = world_bbox(field)
    return {"field_size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2)], "moved_by_m": [round(-c, 2) for c in centre]}


def export_parts(out: Path) -> list[dict]:
    out.mkdir(parents=True, exist_ok=True)
    parts = []
    for src, part in PARTS.items():
        ob = bpy.data.objects.get(src)
        if not ob:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        ob.name = f"SM_{VENUE}_{part}"
        f = out / f"SM_{VENUE}_{part}.fbx"
        bpy.ops.export_scene.fbx(filepath=str(f), use_selection=True, apply_unit_scale=True,
                                 axis_forward="-Y", axis_up="Z", mesh_smooth_type="FACE", add_leaf_bones=False)
        tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        parts.append({"file": f.name, "part": part, "source_object": src, "tris": tris})
    return parts


def ue(loc):
    return [round(loc[0] * 100, 1), round(-loc[1] * 100, 1), round(loc[2] * 100, 1)]


def markers(frame: dict) -> list[dict]:
    m = []

    def add(id, type, loc, **kw):
        m.append({"id": id, "type": type, "loc_m": loc, "ue_loc_cm": ue(loc), **kw})

    deck_z = 2.5
    add("Zone_MainDeck", "stage_zone", [-63.0, 0, deck_z], size_m=[18, 60, 0])
    add("Zone_Field", "crowd_zone", [0, 0, 0], size_m=frame["field_size_m"] + [2.0], section="FIELD_GA")
    add("Zone_Pit", "crowd_zone", [-52.5, 0, 0], size_m=[2.0, 60, 2.0], note="security only")
    add("Zone_FOH", "crowd_zone", [10.0, 0, 0.6], size_m=[8, 10, 3])
    for id, x in [("Mark_Upstage", -68.0), ("Mark_Center", -63.0), ("Mark_Downstage", -56.0), ("Mark_Midfield", 0.0)]:
        add(id, "performer_mark", [x, 0, deck_z])
    add("Rig_CenterBoard", "rig_point", [0, 0, 55.0], note="Centre board; trim or hide for in-the-round kits.")
    for id, loc in [("Cam_FOH", [12, 0, 4]), ("Cam_Pit_SL", [-52, 18, 1.5]), ("Cam_Pit_SR", [-52, -18, 1.5]),
                    ("Cam_Upper_SL", [40, 70, 35]), ("Cam_Upper_SR", [40, -70, 35]), ("Cam_Wide", [90, 0, 45])]:
        add(id, "camera", loc)
    return m


def main() -> None:
    import sys
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--obj", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=Path("unreal/SourceArt/Venues") / VENUE)
    ap.add_argument("--markers-only", action="store_true", help="Skip FBX export; just write markers.json.")
    a = ap.parse_args(argv)

    import_obj(a.obj)
    removed = debrand()
    frame = normalise_frame()
    parts = [] if a.markers_only else export_parts(a.out)
    a.out.mkdir(parents=True, exist_ok=True)
    doc = {
        "venue": VENUE,
        "title": "Stadium (de-branded, from a purchased stadium model; licence check pending)",
        "notes": "Real-venue name and logo removed. Do not ship until the model licence and real-venue likeness are cleared (docs/venues/stadium_main.md).",
        "units": "loc_m: metres, Z up, stage at -X, field centre at origin. ue_loc_cm: Unreal cm (Y flipped).",
        "removed_branding": removed,
        "frame": frame,
        "capacity": {"note": "estimate; the source seats are one merged mesh", "end_stage_concert_total_est": 70000},
        "parts": parts,
        "markers": markers(frame),
    }
    (a.out / "markers.json").write_text(json.dumps(doc, indent=2) + "\n")
    print(json.dumps({k: doc[k] for k in ("removed_branding", "frame")}, indent=2), f"\n{len(parts)} parts -> {a.out}")


if __name__ == "__main__":
    main()
