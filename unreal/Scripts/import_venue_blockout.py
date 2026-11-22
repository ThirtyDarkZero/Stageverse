"""Import a StageVerse venue blockout into Unreal and lay out its markers.

What it does, per venue:
  1. Imports every SM_<Venue>_*.fbx from unreal/SourceArt/Venues/<Venue>/ into
     /Game/Venues/<Venue>/Blockout/ (one static mesh per object, pivots at the
     venue origin, Nanite on, complex collision used as simple).
  2. Creates the level /Game/Venues/<Venue>/Maps/<Venue>_Blockout with basic
     sky lighting and places every mesh at the origin.
  3. Spawns the markers from markers.json: CineCameraActors for camera spots
     (with focal length), TriggerBoxes for stage/crowd zones and bars, and
     tagged TargetPoints for rig points, performer marks, FX and vomitories.
     Everything lands in World Outliner folders under Venue_<Venue>/.

seats.json is not spawned here; it feeds the CrowdKit instanced crowd.

How to run (Editor, Python Editor Script Plugin enabled):
  * Tools > Execute Python Script... and pick this file (imports both venues), or
  * Output Log, Cmd/Python:  py "<repo>/unreal/Scripts/import_venue_blockout.py" Arena_Main
    Add --no-grid to skip the ~230 roof rig-grid points.
"""
import json
import os
import sys

import unreal

VENUES = ["Arena_Main", "Theater_Main"]


def source_root():
    here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None
    candidates = []
    if here:
        candidates.append(os.path.normpath(os.path.join(here, "..", "SourceArt", "Venues")))
    candidates.append(os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()),
                                   "SourceArt", "Venues"))
    for c in candidates:
        if os.path.isdir(c):
            return c
    raise RuntimeError("Could not find SourceArt/Venues next to this script or the project: %s" % candidates)


def cm(v):
    return unreal.Vector(float(v[0]), float(v[1]), float(v[2]))


def rot(r):
    return unreal.Rotator(roll=float(r.get("roll", 0.0)), pitch=float(r.get("pitch", 0.0)),
                          yaw=float(r.get("yaw", 0.0)))


def import_fbx(path, dest):
    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = dest
    task.automated = True
    task.replace_existing = True
    task.save = True
    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_as_skeletal = False
    ui.import_animations = False
    ui.import_materials = True
    ui.import_textures = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    sm = ui.static_mesh_import_data
    sm.combine_meshes = False
    sm.auto_generate_collision = False
    sm.generate_lightmap_u_vs = False
    try:
        sm.build_nanite = True
    except Exception:
        pass
    task.options = ui
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return list(task.imported_object_paths or [])


def set_complex_collision(mesh):
    try:
        bs = mesh.get_editor_property("body_setup")
        if bs:
            bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    except Exception as e:  # non-fatal: set it by hand in the mesh editor
        unreal.log_warning("collision not set on %s: %s" % (mesh.get_name(), e))


def spawn(cls, loc, r, label, folder, tags=()):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = eas.spawn_actor_from_class(cls, loc, r)
    a.set_actor_label(label)
    a.set_folder_path(folder)
    if tags:
        a.set_editor_property("tags", [unreal.Name(t) for t in tags])
    return a


def build_venue(venue, include_grid=True):
    root = os.path.join(source_root(), venue)
    meta = json.load(open(os.path.join(root, "markers.json")))
    dest = "/Game/Venues/%s/Blockout" % venue

    # Use the legacy FBX importer so the FbxImportUI options above apply (5.5+ defaults to Interchange).
    unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX false")
    meshes = []
    try:
        for part in meta["parts"]:
            for p in import_fbx(os.path.join(root, part["file"]), dest):
                asset = unreal.EditorAssetLibrary.load_asset(p.split(".")[0])
                if isinstance(asset, unreal.StaticMesh):
                    set_complex_collision(asset)
                    meshes.append((part["part"], asset))
    finally:
        unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX true")

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_path = "/Game/Venues/%s/Maps/%s_Blockout" % (venue, venue)
    if unreal.EditorAssetLibrary.does_asset_exist(level_path):
        les.load_level(level_path)
    else:
        les.new_level(level_path)

    base = "Venue_%s" % venue
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():  # re-runs replace the previous blockout
        if str(a.get_folder_path()).startswith(base):
            eas.destroy_actor(a)

    zero, norot = unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
    if not any(isinstance(a, unreal.DirectionalLight) for a in eas.get_all_level_actors()):
        sun = spawn(unreal.DirectionalLight, unreal.Vector(0, 0, 5000), unreal.Rotator(roll=0, pitch=-50, yaw=35),
                    "Sun", base + "/Lighting")
        sun.light_component.set_editor_property("atmosphere_sun_light", True)
        spawn(unreal.SkyAtmosphere, zero, norot, "SkyAtmosphere", base + "/Lighting")
        spawn(unreal.SkyLight, zero, norot, "SkyLight", base + "/Lighting").light_component.set_editor_property(
            "real_time_capture", True)
        spawn(unreal.ExponentialHeightFog, zero, norot, "Fog", base + "/Lighting")

    for part, mesh in meshes:
        a = eas.spawn_actor_from_object(mesh, zero, norot)
        a.set_actor_label(mesh.get_name())
        a.set_folder_path("%s/Geometry/%s" % (base, part))

    for m in meta["markers"]:
        t = m["type"]
        if t == "rig_grid" and not include_grid:
            continue
        loc, r = cm(m["ue_loc_cm"]), rot(m["ue_rot_deg"])
        folder = "%s/Markers/%s" % (base, t)
        tags = ["SV_" + t, m["id"]]
        if t == "camera":
            a = spawn(unreal.CineCameraActor, loc, r, m["id"], folder, tags)
            try:
                a.get_cine_camera_component().set_editor_property("current_focal_length", float(m.get("lens_mm", 35)))
            except Exception:
                pass
        elif "ue_size_cm" in m:
            a = spawn(unreal.TriggerBox, loc, r, m["id"], folder, tags)
            sx, sy, sz = (max(float(v), 20.0) / 2 for v in m["ue_size_cm"])
            box = a.get_component_by_class(unreal.BoxComponent)
            box.set_editor_property("box_extent", unreal.Vector(sx, sy, sz))
        else:
            spawn(unreal.TargetPoint, loc, r, m["id"], folder, tags)

    les.save_current_level()
    cap = meta.get("capacity", {})
    unreal.log("StageVerse: %s blockout imported: %d meshes, %d markers, capacity %s" %
               (venue, len(meshes), len(meta["markers"]), cap))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    include_grid = "--no-grid" not in sys.argv
    for v in (args or VENUES):
        build_venue(v, include_grid)


main()
