"""Import a rigged performer (FBX) and stand them on a performer mark of a stage kit (UE 5.3).

Run headless with the Unreal Editor CLOSED:
  UnrealEditor-Cmd <Project>.uproject -run=pythonscript -script="<repo>/unreal/Scripts/place_performer.py --kit <repo>/content/stages/stadium/stadium_horizon.json --level /Game/Venues/Stadium_Main/Stadium_Main_Blockout --fbx <repo>/unreal/SourceArt/Characters/ArizonaRae/SK_ArizonaRae.fbx"

What it does:
  - Imports the FBX as a skeletal mesh (with its own skeleton, materials and textures) into
    /Game/Characters/<Name>. Skipped if it is already there, unless --reimport.
  - Spawns her on the chosen mark (default "center") on top of the deck, facing the audience (+X),
    filed under Show/<stageKit>/Performers. Re-running replaces the previous one.
  --yaw turns her if she faces the wrong way (default -90; try 90 or 0).
"""
import argparse
import json
import os
import shlex
import sys

import unreal


def log(msg):
    unreal.log(f"[StageVerse] {msg}")


def args():
    argv = sys.argv[1:]
    if len(argv) == 1 and " " in argv[0]:
        argv = shlex.split(argv[0])
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--level", required=True)
    ap.add_argument("--fbx", required=True)
    ap.add_argument("--name", default="ArizonaRae")
    ap.add_argument("--mark", default="center")
    ap.add_argument("--yaw", type=float, default=-90.0)  # FBX from Blender faces +Y; -90 turns her to the audience (+X)
    ap.add_argument("--reimport", action="store_true")
    return ap.parse_args(argv)


def sub():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def ue(x, y, z):
    return unreal.Vector(x * 100.0, -y * 100.0, z * 100.0)


def import_fbx(fbx, name, reimport):
    dest = f"/Game/Characters/{name}"
    mesh_path = f"{dest}/SK_{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(mesh_path) and not reimport:
        log(f"using existing {mesh_path}")
        return unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not os.path.isfile(fbx):
        raise RuntimeError(f"FBX not found: {fbx} (did git lfs pull run?)")
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", True)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    ui.set_editor_property("import_materials", True)
    ui.set_editor_property("import_textures", True)
    ui.set_editor_property("import_animations", False)
    ui.set_editor_property("create_physics_asset", True)
    ui.skeletal_mesh_import_data.set_editor_property("import_morph_targets", True)
    ui.skeletal_mesh_import_data.set_editor_property("convert_scene", True)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx)
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("destination_name", f"SK_{name}")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", ui)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    for p in task.get_editor_property("imported_object_paths"):
        a = unreal.EditorAssetLibrary.load_asset(p)
        if isinstance(a, unreal.SkeletalMesh):
            log(f"imported {p}")
            return a
    raise RuntimeError(f"no skeletal mesh came out of {fbx}: {list(task.get_editor_property('imported_object_paths'))}")


def floor_top():
    for a in sub().get_all_level_actors():
        if a.get_actor_label() == "Floor_ConcreteSubfloor":
            o, e = a.get_actor_bounds(False)
            return (o.z + e.z) / 100.0
    return 0.0


def main():
    a = args()
    kit = json.load(open(a.kit))
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(a.level):
        raise RuntimeError(f"could not load {a.level}")
    mesh = import_fbx(a.fbx, a.name, a.reimport)
    mark = next((m for m in kit["marks"] if m["id"] == a.mark), None)
    if not mark:
        raise RuntimeError(f"mark {a.mark} not in {kit['stageKit']}: {[m['id'] for m in kit['marks']]}")
    folder = f"Show/{kit['stageKit']}/Performers"
    for old in list(sub().get_all_level_actors()):
        if old.get_actor_label() == a.name and str(old.get_folder_path()).startswith(folder):
            sub().destroy_actor(old)
    loc = ue(mark["x"], mark["y"], floor_top() + mark["z"])
    actor = sub().spawn_actor_from_class(unreal.SkeletalMeshActor, loc, unreal.Rotator(0, 0, a.yaw))
    comp = actor.get_editor_property("skeletal_mesh_component")
    comp.set_skeletal_mesh_asset(mesh) if hasattr(comp, "set_skeletal_mesh_asset") else comp.set_skeletal_mesh(mesh)
    # stand her feet on the deck: lift by however far the mesh reaches below its pivot
    o, e = actor.get_actor_bounds(False)
    lift = loc.z - (o.z - e.z)
    if abs(lift) > 1.0:
        actor.set_actor_location(unreal.Vector(loc.x, loc.y, loc.z + lift), False, False)
    actor.set_actor_label(a.name)
    actor.set_folder_path(folder)
    o, e = actor.get_actor_bounds(False)
    log(f"{a.name} on mark '{a.mark}' at {actor.get_actor_location()}, height {e.z * 2 / 100.0:.2f} m")
    les.save_current_level()
    log("performer placed")


main()
