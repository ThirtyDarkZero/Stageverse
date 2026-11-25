"""Night show look for a venue level with a stage kit built by build_stage_kit.py (UE 5.3).

Run headless with the Unreal Editor CLOSED:
  UnrealEditor-Cmd <Project>.uproject -run=pythonscript -script="<repo>/unreal/Scripts/night_look.py --kit <repo>/content/stages/stadium/stadium_horizon.json --level /Game/Venues/Stadium_Main/Stadium_Main_Blockout"

What it does:
  - Sun becomes a dim blue moonlight (Movable, so no "lighting needs to be rebuilt").
  - Sky light low; height fog turned into stage haze with volumetric fog so beams show.
  - Unbound post-process volume: fixed exposure (so the night stays dark and LEDs glow), bloom.
  - Lighting rig from the kit: follow spots from front of house on every performer mark,
    and beam fixtures on top of every tall LED surface, fanning out over the crowd and up,
    in the brand palette (Laser Ice / Riot Red / Wheatpaste).
All rig actors go in Show/<stageKit>/Lights and are rebuilt on every run.
Each property set is guarded: an unknown property logs a warning instead of stopping the script.
"""
import argparse
import json
import shlex
import sys

import unreal

ICE = unreal.LinearColor(0.66, 0.91, 1.0, 1.0)
RED = unreal.LinearColor(1.0, 0.12, 0.18, 1.0)
PAPER = unreal.LinearColor(0.95, 0.93, 0.91, 1.0)
MOON = unreal.LinearColor(0.55, 0.65, 1.0, 1.0)


def log(msg):
    unreal.log(f"[StageVerse] {msg}")


def setp(obj, prop, value):
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception as exc:  # property names move between engine versions
        unreal.log_warning(f"[StageVerse] could not set {prop} on {obj.get_name()}: {exc}")
        return False


def args():
    argv = sys.argv[1:]
    if len(argv) == 1 and " " in argv[0]:
        argv = shlex.split(argv[0])
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--level", required=True)
    # Follow-spot strength in candelas. The night exposure is set very bright (bias 10) so the dark bowl reads;
    # 400000 cd blew the performer out to white, so a key of ~8000 cd keeps skin and costume detail.
    ap.add_argument("--follow-cd", type=float, default=8000.0)
    return ap.parse_args(argv)


def sub():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def all_of(cls):
    return [a for a in sub().get_all_level_actors() if isinstance(a, cls)]


def ue(x, y, z):
    return unreal.Vector(x * 100.0, -y * 100.0, z * 100.0)


def movable(actor):
    root = actor.get_editor_property("root_component")
    if root:
        root.set_mobility(unreal.ComponentMobility.MOVABLE)


# ---------------- environment ----------------
def environment():
    for sun in all_of(unreal.DirectionalLight):
        movable(sun)
        c = sun.get_editor_property("light_component")
        setp(c, "intensity", 0.08)
        setp(c, "light_color", unreal.Color(140, 165, 255, 255))
        sun.set_actor_rotation(unreal.Rotator(0, -35, 40), False)  # roll, pitch, yaw
        log(f"sun -> moonlight ({sun.get_actor_label()})")
    for sky in all_of(unreal.SkyLight):
        movable(sky)
        c = sky.get_editor_property("light_component")
        setp(c, "intensity", 0.2)
        try:
            c.recapture_sky()
        except Exception:
            pass
    for fog in all_of(unreal.ExponentialHeightFog):
        c = fog.get_editor_property("component")
        setp(c, "fog_density", 0.035)
        setp(c, "fog_height_falloff", 0.02)
        if not setp(c, "fog_inscattering_luminance", unreal.LinearColor(0.01, 0.012, 0.02, 1)):
            setp(c, "fog_inscattering_color", unreal.LinearColor(0.01, 0.012, 0.02, 1))
        setp(c, "volumetric_fog", True)
        setp(c, "volumetric_fog_scattering_distribution", 0.6)
        setp(c, "volumetric_fog_extinction_scale", 1.5)
        log("height fog -> stage haze (volumetric)")

    for ppv in [a for a in all_of(unreal.PostProcessVolume) if a.get_actor_label() == "SV_NightPost"]:
        sub().destroy_actor(ppv)
    ppv = sub().spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
    ppv.set_actor_label("SV_NightPost")
    ppv.set_folder_path("Show/Look")
    setp(ppv, "unbound", True)
    s = ppv.get_editor_property("settings")
    for prop, val in [
        ("override_auto_exposure_method", True), ("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL),
        ("override_auto_exposure_bias", True), ("auto_exposure_bias", 10.0),  # tuned by eye on Rob's Mac 2026-11-24
        ("override_bloom_intensity", True), ("bloom_intensity", 1.2),
        ("override_vignette_intensity", True), ("vignette_intensity", 0.5),
    ]:
        setp(s, prop, val)
    setp(ppv, "settings", s)
    log("post-process: manual exposure, bloom")


# ---------------- rig ----------------
def spot(label, folder, loc, target, color, cone, intensity_cd, shadows=False, haze=4.0):
    rot = unreal.MathLibrary.find_look_at_rotation(loc, target)
    a = sub().spawn_actor_from_class(unreal.SpotLight, loc, rot)
    a.set_actor_label(label)
    a.set_folder_path(folder)
    c = a.get_editor_property("spot_light_component")
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    setp(c, "intensity_units", unreal.LightUnits.CANDELAS)
    setp(c, "intensity", intensity_cd)
    setp(c, "light_color", unreal.Color(int(color.r * 255), int(color.g * 255), int(color.b * 255), 255))
    setp(c, "outer_cone_angle", cone)
    setp(c, "inner_cone_angle", cone * 0.6)
    setp(c, "attenuation_radius", 25000.0)
    setp(c, "volumetric_scattering_intensity", haze)
    setp(c, "cast_shadows", shadows)
    return a


def rig(kit, floor_z, follow_cd=8000.0):
    folder = f"Show/{kit['stageKit']}/Lights"
    for a in list(sub().get_all_level_actors()):
        if str(a.get_folder_path()).startswith(folder):
            sub().destroy_actor(a)
    n = 0
    # Follow spots: from front of house (downstage, high), on every performer mark.
    decks = [e for e in kit["elements"] if e["kind"] == "deck" and e["shape"] == "rect"]
    stage_front = max((e["x"] + e["w"] / 2 for e in decks if e["x"] < 0), default=0.0)
    for i, m in enumerate(kit["marks"]):
        src = ue(m["x"] + 45.0, (-12 if i % 2 else 12), floor_z + 22.0)
        dst = ue(m["x"], m["y"], floor_z + m["z"] + 1.0)
        spot(f"Follow_{m['id']}", folder, src, dst, PAPER, 3.0, follow_cd, shadows=True, haze=0.3)
        n += 1
    # Beams on top of every tall LED surface: one out over the crowd, one up into the roof.
    palette = [ICE, RED, PAPER]
    for i, e in enumerate([e for e in kit["elements"] if e["kind"] == "led_surface" and e.get("h", 0) >= 8]):
        top = floor_z + e["z"] + e["h"] + 0.5
        base = ue(e["x"], e["y"], top)
        crowd = ue(e["x"] + 90.0, e["y"] * 2.2, floor_z)
        sky = ue(e["x"] + 15.0, e["y"] * 1.4, top + 60.0)
        col = palette[i % len(palette)]
        spot(f"Beam_{e['id']}_crowd", folder, base, crowd, col, 2.5, 600000.0)
        spot(f"Beam_{e['id']}_sky", folder, base, sky, col, 2.0, 600000.0)
        n += 2
    # Floor beams along the downstage edge, crossing in a fan.
    width = max((e["d"] for e in decks if e["x"] < 0), default=20.0)
    for i in range(8):
        y = -width / 2 + width * (i + 0.5) / 8
        src = ue(stage_front - 0.5, y, floor_z + 2.8)
        dst = ue(stage_front + 40.0, -y * 1.8, floor_z + 45.0)
        spot(f"Beam_floor_{i+1}", folder, src, dst, ICE if i % 2 else RED, 2.0, 300000.0)
        n += 1
    log(f"rig: {n} fixtures")


def led_night(kit):
    """Swap LED surfaces to a softer, saturated night material so they glow instead of clipping to white."""
    path = "/Game/StageVerse/Materials/M_SV_LED_Night"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat = unreal.EditorAssetLibrary.load_asset(path)
    else:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_SV_LED_Night", "/Game/StageVerse/Materials", unreal.Material, unreal.MaterialFactoryNew())
        mel = unreal.MaterialEditingLibrary
        base = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
        base.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 1))
        mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
        emi = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 200)
        emi.set_editor_property("constant", unreal.LinearColor(0.05, 0.22, 0.9, 1))  # deep Laser Blue/Ice glow
        mel.connect_material_property(emi, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat)
    ids = {e["id"] for e in kit["elements"] if e["kind"] == "led_surface"}
    n = 0
    for a in sub().get_all_level_actors():
        label = a.get_actor_label()
        if label.startswith(kit["stageKit"] + "_") and label[len(kit["stageKit"]) + 1:] in ids:
            a.static_mesh_component.set_material(0, mat)
            n += 1
    log(f"LED surfaces -> night material ({n})")


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
    environment()
    led_night(kit)
    rig(kit, floor_top(), a.follow_cd)
    les.save_current_level()
    log("night look done")


main()
