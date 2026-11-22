# Venue blockouts

Script-generated greybox venues in real-world meters. They are **layout blockouts**, not final art:
they fix the scale, sightlines, capacities, stage zones, rigging and camera positions. Rob dresses
them in Unreal with the bought Fab packs (International Arena shell, Concert Arena Stage kit) and
keeps the markers and seat points as the source of truth.

| Venue | Spirit of | Capacity (generated) |
| --- | --- | --- |
| `Arena_Main` | Downtown NBA/NHL arena, two-tier oval bowl, suite ring, centre-hung board | 22,260 bowl seats in the round; **~18,650 end-stage concert** (15,037 sold bowl seats + 2,463 floor GA at 2.5/m² + ~1,150 suite seats) |
| `Theater_Main` | Downtown LA music theater, GA floor + balcony, proscenium stage | **~2,380** (1,884 floor GA at 2.5/m² + 315 balcony seats + 180 side-gallery spots) |

Both are original designs: no real names, logos, signage or signature rooflines. The SoFi Stadium
OBJ in project files was used only as a real-world scale sanity check (it is a branded copy of a real
building, so none of its geometry is used or shipped).

## Build

```bash
# bpy wheel (Blender 5.0) needs Python 3.11
uv venv -p 3.11 .bpy && VIRTUAL_ENV=.bpy uv pip install bpy==5.0.1 matplotlib
.bpy/bin/python pipeline/venues/build_venues.py all            # ~4 min with Cycles previews
.bpy/bin/python pipeline/venues/build_venues.py arena --no-render
# or with a Blender install:  blender -b -P pipeline/venues/build_venues.py -- all
```

Outputs land in `unreal/SourceArt/Venues/<Venue>/`:

| File | What |
| --- | --- |
| `SM_<Venue>_<Part>.fbx` | One FBX per modular part (bowl tiers hold one mesh per seating section). Pivots at the venue origin, so every part drops in at 0,0,0. |
| `markers.json` | Capacity, part list and every marker: `rig_grid`, `rig_point`, `rig_lineset`, `camera`, `stage_zone`, `crowd_zone`, `bar`, `performer_mark`, `fx_point`, `vomitory`. Each has `loc_m` (Blender) and `ue_loc_cm` / `ue_rot_deg` (Unreal). |
| `seats.json` | Crowd instance points per section: `[x_cm, y_cm, z_cm, yaw_deg, row, view]` in Unreal space. `view` 0 clear, 1 limited, 2 not sold in the end-stage config. Floor GA sections are standing spots at the stated density. |
| `previews/` | Cycles greybox renders and a plan diagram with sections, zones, rig points and cameras. |

## Conventions

- Meters, Z up, **stage at -X**, venue symmetric about X. Unreal flips Y on import; because of the
  symmetry nothing moves, and the JSON already carries Unreal-space values.
- Material slots are stable greybox names (`M_GB_SeatLower`, `M_GB_StageDeck`, `M_GB_LED`, ...).
  Swap them for Fab material instances in Unreal, never rename them in the generator.
- UVs are world-aligned box projection at 1 m, so tiling materials work straight away.
- Tune the design by editing the constants at the top of `arena.py` / `theater.py` and rebuilding.

## Into Unreal

`unreal/Scripts/import_venue_blockout.py` imports the FBX files, creates
`/Game/Venues/<Venue>/Maps/<Venue>_Blockout`, places the meshes and spawns the markers
(CineCameraActors, TriggerBoxes for zones, tagged TargetPoints for rig points and marks).
See the script header for how to run it.
