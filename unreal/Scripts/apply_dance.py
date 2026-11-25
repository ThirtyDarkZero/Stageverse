"""Import a dance animation (FBX) onto a performer's skeleton and make her perform it on loop (UE 5.3).

Run headless with the Unreal Editor CLOSED, after place_performer.py:
  UnrealEditor-Cmd <Project>.uproject -run=pythonscript -script="<repo>/unreal/Scripts/apply_dance.py --level /Game/Venues/Stadium_Main/Stadium_Main_Blockout --fbx <repo>/unreal/SourceArt/Characters/ArizonaRae/Anims/A_ArizonaRae_Telephone.fbx"

What it does:
  - Imports the FBX as an animation sequence for /Game/Characters/<Name>/SK_<Name>'s skeleton
    (into /Game/Characters/<Name>/Anims). Re-running replaces it.
  - Finds the performer actor labelled <Name> in the level and sets it to play that animation on loop,
    also in the editor viewport. Press Play (or Simulate) to watch it with the show running.
"""
import argparse
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
    ap.add_argument("--level", required=True)
    ap.add_argument("--fbx", required=True)
    ap.add_argument("--name", default="ArizonaRae")
    return ap.parse_args(argv)


def import_anim(fbx, name):
    mesh_path = f"/Game/Characters/{name}/SK_{name}"
    if not unreal.EditorAssetLibrary.does_asset_exist(mesh_path):
        raise RuntimeError(f"{mesh_path} not found: run place_performer.py first")
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    skeleton = mesh.get_editor_property("skeleton")
    if not os.path.isfile(fbx):
        raise RuntimeError(f"FBX not found: {fbx} (did git lfs pull run?)")
    anim_name = os.path.splitext(os.path.basename(fbx))[0]
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", False)
    ui.set_editor_property("import_as_skeletal", True)
    ui.set_editor_property("import_animations", True)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("skeleton", skeleton)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    ui.anim_sequence_import_data.set_editor_property("convert_scene", True)
    ui.anim_sequence_import_data.set_editor_property("convert_scene_unit", True)  # metres -> cm, same as the mesh
    ui.anim_sequence_import_data.set_editor_property("import_bone_tracks", True)
    ui.anim_sequence_import_data.set_editor_property("remove_redundant_keys", False)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx)
    task.set_editor_property("destination_path", f"/Game/Characters/{name}/Anims")
    task.set_editor_property("destination_name", anim_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", ui)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    for p in task.get_editor_property("imported_object_paths"):
        a = unreal.EditorAssetLibrary.load_asset(p)
        if isinstance(a, unreal.AnimSequence):
            log(f"imported animation {p} ({a.get_editor_property('sequence_length'):.1f} s)")
            return a
    raise RuntimeError(f"no animation came out of {fbx}: {list(task.get_editor_property('imported_object_paths'))}")


def main():
    a = args()
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(a.level):
        raise RuntimeError(f"could not load {a.level}")
    anim = import_anim(a.fbx, a.name)
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = [x for x in sub.get_all_level_actors() if x.get_actor_label() == a.name and isinstance(x, unreal.SkeletalMeshActor)]
    if not actors:
        raise RuntimeError(f"no performer labelled {a.name} in the level: run place_performer.py first")
    for actor in actors:
        comp = actor.get_editor_property("skeletal_mesh_component")
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        comp.override_animation_data(anim, True, True, 0.0, 1.0)  # anim, looping, playing, start, rate
        try:
            comp.set_update_animation_in_editor(True)
        except Exception as exc:
            unreal.log_warning(f"[StageVerse] editor preview not available: {exc}")
        log(f"{a.name} now performs {anim.get_name()} on loop")
    les.save_current_level()
    log("dance applied")


main()
