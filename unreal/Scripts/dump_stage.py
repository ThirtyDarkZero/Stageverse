"""Print where the stage, marks, performer and floor really are in a level (UE 5.3), for debugging placement.

  UnrealEditor-Cmd <Project>.uproject -run=pythonscript -script="<repo>/unreal/Scripts/dump_stage.py --level /Game/Venues/Stadium_Main/Stadium_Main_Blockout --kit stadium_horizon"
"""
import argparse
import shlex
import sys

import unreal

argv = sys.argv[1:]
if len(argv) == 1 and " " in argv[0]:
    argv = shlex.split(argv[0])
ap = argparse.ArgumentParser()
ap.add_argument("--level", required=True)
ap.add_argument("--kit", default="stadium_horizon")
a = ap.parse_args(argv)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(a.level)
for x in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    label, folder = x.get_actor_label(), str(x.get_folder_path())
    if not (folder.startswith("Show") or label.startswith("Floor") or label.startswith("SM_Stadium_Main_Field")
            or isinstance(x, (unreal.PlayerStart, unreal.SkeletalMeshActor))):
        continue
    if "_column_" in label or label.startswith("Beam_") or "_ring" in label:
        continue
    o, e = x.get_actor_bounds(False)
    unreal.log(f"[StageVerse] {label:32s} {folder:34s} loc={x.get_actor_location()} "
               f"bottom_z={(o.z - e.z) / 100:.2f}m top_z={(o.z + e.z) / 100:.2f}m x={(o.x - e.x) / 100:.1f}..{(o.x + e.x) / 100:.1f}m "
               f"y={(o.y - e.y) / 100:.1f}..{(o.y + e.y) / 100:.1f}m")
