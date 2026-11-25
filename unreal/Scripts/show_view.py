"""Put the performer back on her mark and give Play a front-row view of the stage (UE 5.3).

Run headless with the Unreal Editor CLOSED:
  UnrealEditor-Cmd <Project>.uproject -run=pythonscript -script="<repo>/unreal/Scripts/show_view.py --kit <repo>/content/stages/stadium/stadium_horizon.json --level /Game/Venues/Stadium_Main/Stadium_Main_Blockout"

What it does:
  - Stands the performer (default ArizonaRae) on the kit mark (default "center"): X/Y on the mark,
    feet on the top of the deck under it, facing the audience. Logs where she was and where she is now.
  - Adds a PlayerStart in the front row (just behind the barricade, eye height, looking at her), so
    pressing Play starts you in the audience instead of wherever the engine drops you.
"""
import argparse
import json
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
    ap.add_argument("--name", default="ArizonaRae")
    ap.add_argument("--mark", default="center")
    ap.add_argument("--yaw", type=float, default=-90.0)
    ap.add_argument("--row-distance", type=float, default=14.0, help="metres from her to the front-row camera")
    return ap.parse_args(argv)


def ue(x, y, z):
    return unreal.Vector(x * 100.0, -y * 100.0, z * 100.0)


def main():
    a = args()
    kit = json.load(open(a.kit))
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(a.level):
        raise RuntimeError(f"could not load {a.level}")
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    acts = sub.get_all_level_actors()
    mark = next(m for m in kit["marks"] if m["id"] == a.mark)
    perf = next((x for x in acts if x.get_actor_label() == a.name and isinstance(x, unreal.SkeletalMeshActor)), None)
    if not perf:
        raise RuntimeError(f"no performer labelled {a.name}: run place_performer.py first")
    log(f"{a.name} was at {perf.get_actor_location()} rot {perf.get_actor_rotation()}")

    # deck top: the highest kit deck actor whose footprint contains the mark
    target = ue(mark["x"], mark["y"], 0)
    deck_top = None
    for x in acts:
        if not x.get_actor_label().startswith(kit["stageKit"] + "_") or not isinstance(x, unreal.StaticMeshActor):
            continue
        o, e = x.get_actor_bounds(False)
        if abs(target.x - o.x) <= e.x and abs(target.y - o.y) <= e.y and e.z < 1000:
            top = o.z + e.z
            if top < 2000 and (deck_top is None or top > deck_top):
                deck_top = top
    if deck_top is None:
        raise RuntimeError("no deck found under the mark")
    log(f"deck top under mark '{a.mark}': {deck_top / 100.0:.2f} m")

    # feet on the deck: pivot of the Meshy rig is at the feet (Blender origin at the soles)
    comp = perf.get_editor_property("skeletal_mesh_component")
    perf.set_actor_location(unreal.Vector(target.x, target.y, deck_top), False, False)
    perf.set_actor_rotation(unreal.Rotator(0, 0, a.yaw), False)
    perf.set_actor_scale3d(unreal.Vector(1, 1, 1))
    comp.set_editor_property("relative_location", unreal.Vector(0, 0, 0))
    log(f"{a.name} now at {perf.get_actor_location()} (mark {a.mark})")

    # front-row PlayerStart looking at her chest
    for x in acts:
        if isinstance(x, unreal.PlayerStart):
            if x.get_actor_label() == "SV_FrontRow":
                sub.destroy_actor(x)
            else:
                unreal.log_warning(f"[StageVerse] another PlayerStart exists ({x.get_actor_label()}); Play may use it instead")
    eye = unreal.Vector(target.x + a.row_distance * 100.0, target.y, deck_top - 250.0 + 170.0)  # standing on the floor (deck is 2.5 m), eyes at 1.7 m
    look = unreal.MathLibrary.find_look_at_rotation(eye, unreal.Vector(target.x, target.y, deck_top + 120.0))
    ps = sub.spawn_actor_from_class(unreal.PlayerStart, eye, look)
    ps.set_actor_label("SV_FrontRow")
    ps.set_folder_path(f"Show/{kit['stageKit']}/Cameras")
    log(f"front-row PlayerStart at {eye}, {a.row_distance:.0f} m from her")
    les.save_current_level()
    log("show view ready: press Play")


main()
