"""Build a StageVerse stage kit (content/stages/<tier>/<kit>.json) into a venue level.

Run headless with the Unreal Editor CLOSED (UE 5.3):
  UnrealEditor-Cmd <Project>.uproject -run=pythonscript -script="<repo>/unreal/Scripts/build_stage_kit.py --kit <repo>/content/stages/stadium/stadium_horizon.json --level /Game/Venues/Stadium_Main/Stadium_Main_Blockout --floor"

Or from the editor's Output Log (Cmd: Python): py "<path>/build_stage_kit.py" --kit ... --level ...

What it does (producer order: floor first, then the show from the back of the centre beam forward):
  --floor : hides the goalposts and lays a concrete sub-floor over the whole field level
            (sized from the field-surround mesh), plus a front-of-stage barricade.
  kit     : places every element of the stage design as greybox geometry with a material per
            kind (deck, LED, kinetic, truss, scrim...), performer marks and FX positions as
            labelled TargetPoints, all filed under the Outliner folder Show/<stageKit>.
Re-running removes the previous Show/<stageKit> actors first, so it is safe to repeat.

Units: kit files are metres in the venue frame (Z up, stage at -X); Unreal = cm, Y flipped.
Note: spawn actors by class (spawn_actor_from_object crashes in the pythonscript commandlet).
"""
import argparse
import json
import math
import shlex
import sys

import unreal

MAT_DIR = "/Game/StageVerse/Materials"
CUBE = "/Engine/BasicShapes/Cube.Cube"          # 100 cm cube, pivot at centre
CYL = "/Engine/BasicShapes/Cylinder.Cylinder"   # 100 cm diameter, 100 cm tall, pivot at centre

# name: (base colour, emissive strength, roughness)
MATERIALS = {
    "M_SV_Concrete":  ((0.20, 0.20, 0.20), 0.0, 0.85),
    "M_SV_Deck":      ((0.02, 0.02, 0.02), 0.0, 0.35),
    "M_SV_LED":       ((0.66, 0.91, 1.00), 4.0, 0.30),   # Laser Ice
    "M_SV_Kinetic":   ((1.00, 0.12, 0.18), 1.5, 0.40),   # Riot Red
    "M_SV_Truss":     ((0.35, 0.35, 0.35), 0.0, 0.50),
    "M_SV_Structure": ((0.95, 0.93, 0.91), 0.0, 0.60),   # Wheatpaste
    "M_SV_Scrim":     ((0.18, 0.42, 1.00), 0.8, 0.60),   # Laser Blue
    "M_SV_Barricade": ((0.12, 0.12, 0.12), 0.0, 0.40),
}
KIND_MAT = {
    "deck": "M_SV_Deck", "lift": "M_SV_Kinetic", "turntable": "M_SV_Deck", "led_surface": "M_SV_LED",
    "kinetic": "M_SV_Kinetic", "truss": "M_SV_Truss", "structure": "M_SV_Structure", "scrim": "M_SV_Scrim",
    "fixture_array": "M_SV_Truss", "fx_zone": "M_SV_Truss",
}
GOALPOST_ACTORS = ["SM_Stadium_Main_FieldMarkings"]  # the source "Target" object = goalposts
FIELD_SURROUND = "SM_Stadium_Main_FieldSurround"
FIELD = "SM_Stadium_Main_Field"


def log(msg):
    unreal.log(f"[StageVerse] {msg}")


def args():
    argv = sys.argv[1:]
    if len(argv) == 1 and " " in argv[0]:
        argv = shlex.split(argv[0])
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--level", required=True)
    ap.add_argument("--floor", action="store_true")
    return ap.parse_args(argv)


# ---------------- materials ----------------
def material(name):
    path = f"{MAT_DIR}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    color, emissive, rough = MATERIALS[name]
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    c = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    c.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 200)
    r.set_editor_property("r", rough)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    if emissive > 0:
        e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 400)
        e.set_editor_property("constant", unreal.LinearColor(*(v * emissive for v in color), 1.0))
        mel.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


# ---------------- spawning ----------------
def actors():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()


def find(label):
    return next((a for a in actors() if a.get_actor_label() == label), None)


def ue(x, y, z):
    return unreal.Vector(x * 100.0, -y * 100.0, z * 100.0)


def box(label, folder, mesh_path, center_m, size_m, mat_name, yaw=0.0):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = sub.spawn_actor_from_class(unreal.StaticMeshActor, ue(*center_m), unreal.Rotator(0, 0, -yaw))
    comp = a.static_mesh_component
    comp.set_static_mesh(unreal.EditorAssetLibrary.load_asset(mesh_path))
    comp.set_material(0, material(mat_name))
    a.set_actor_scale3d(unreal.Vector(max(size_m[0], 0.02), max(size_m[1], 0.02), max(size_m[2], 0.02)))
    a.set_actor_label(label)
    a.set_folder_path(folder)
    return a


def point(label, folder, loc_m):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = sub.spawn_actor_from_class(unreal.TargetPoint, ue(*loc_m))
    a.set_actor_label(label)
    a.set_folder_path(folder)
    return a


def vertical_span(e, floor_z):
    """(bottom, height) in metres for an element. Decks/lifts fill from the floor up to their top."""
    if e["kind"] in ("deck", "lift", "turntable"):
        return floor_z, max(e["z"], 0.1)
    if e.get("h", 0) > 0:
        return floor_z + e["z"], e["h"]
    return floor_z + e["z"], 0.1


def build_element(e, folder, floor_z):
    mat = KIND_MAT[e["kind"]]
    bottom, height = vertical_span(e, floor_z)
    zc = bottom + height / 2
    label = f"{folder.split('/')[-1]}_{e['id']}"
    if e["shape"] == "rect":
        box(label, folder, CUBE, (e["x"], e["y"], zc), (e["w"], e["d"], height), mat)
    elif e["shape"] == "disc":
        box(label, folder, CYL, (e["x"], e["y"], zc), (2 * e["r"], 2 * e["r"], height), mat)
    else:  # ring: segments around the circle
        n = max(24, int(e["r"] * 3))
        seg = 2 * math.pi * e["r"] / n * 1.05
        for i in range(n):
            t = 2 * math.pi * i / n
            x, y = e["x"] + e["r"] * math.cos(t), e["y"] + e["r"] * math.sin(t)
            box(f"{label}_{i:02d}", folder, CUBE, (x, y, zc), (e["width"], seg, max(height, 0.3)), mat,
                yaw=math.degrees(t))


def clear_folder(folder):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in list(actors()):
        if str(a.get_folder_path()).startswith(folder):
            sub.destroy_actor(a)


# ---------------- floor ----------------
def lay_floor():
    folder = "Show/Floor"
    clear_folder(folder)
    for name in GOALPOST_ACTORS:
        a = find(name)
        if a:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
            log(f"removed goalposts actor {name}")
    field = find(FIELD)
    surround = find(FIELD_SURROUND) or field
    if not surround:
        raise RuntimeError("Field meshes not found: is this the Stadium_Main level?")
    origin, extent = surround.get_actor_bounds(False)
    top = 0.0
    if field:
        f_origin, f_extent = field.get_actor_bounds(False)
        top = (f_origin.z + f_extent.z) / 100.0
    thick = 0.15
    size = (extent.x * 2 / 100.0, extent.y * 2 / 100.0, thick)
    box("Floor_ConcreteSubfloor", folder, CUBE, (origin.x / 100.0, -origin.y / 100.0, top + thick / 2), size, "M_SV_Concrete")
    log(f"concrete sub-floor {size[0]:.1f} x {size[1]:.1f} m at z={top + thick:.2f} m")
    return top + thick


def barricade(kit, folder, floor_z):
    decks = [e for e in kit["elements"] if e["kind"] == "deck" and e["shape"] == "rect" and e["x"] < -20]
    if not decks:
        return
    main = min(decks, key=lambda e: e["x"])
    front = main["x"] + main["w"] / 2 + 1.8  # 1.8 m pit between deck and barricade
    box(f"{kit['stageKit']}_barricade", folder, CUBE, (front, 0, floor_z + 0.6), (0.6, main["d"] + 6, 1.2), "M_SV_Barricade")


# ---------------- main ----------------
def main():
    a = args()
    kit = json.load(open(a.kit))
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(a.level):
        raise RuntimeError(f"could not load {a.level}")
    floor_z = lay_floor() if a.floor else 0.0
    folder = f"Show/{kit['stageKit']}"
    clear_folder(folder)
    for e in kit["elements"]:
        build_element(e, folder, floor_z)
    for m in kit["marks"]:
        point(f"Mark_{m['id']}", f"{folder}/Marks", (m["x"], m["y"], floor_z + m["z"]))
    for f in kit["fx"]:
        point(f"FX_{f['id']}", f"{folder}/FX", (f["x"], f["y"], floor_z + f["z"]))
    if a.floor:
        barricade(kit, folder, floor_z)
    les.save_current_level()
    log(f"built {kit['name']} ({len(kit['elements'])} elements) into {a.level}")


main()
