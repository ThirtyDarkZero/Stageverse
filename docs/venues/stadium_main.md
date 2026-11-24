# Stadium_Main (from the purchased stadium model)

**Status:** model licence confirmed by Rob on 2026-11-24; the de-branded mesh is in the repo via Git LFS. The real-venue likeness (check 2) is still open: restyle before public release.

## Source

- File: `sofi-stadium.zip` in project files (bought on Fab). An OBJ replica of a real NFL stadium, exported from Blender 3.6.2, 5.07M tris (4.63M of them one merged seat mesh), low-res JPG textures, no LODs.
- The zip has **no licence file, readme or author credit**, so the licence can only be confirmed from the Fab listing in Rob's library.

## Check 1: model licence (done 2026-11-24, Rob confirmed)

Open the item in your Fab library and note which licence it was bought under:
- **Fab Standard License**: allows use in a distributed commercial game. OK to proceed.
- **Personal licence**: not OK for a released game; re-buy under Standard.
- **CC-BY or similar**: OK with an attribution credit in the game.

Also check the listing for "editorial use" or "no trademarked use" wording. Replica models of real landmarks are often sold for editorial or reference use only.

## Check 2: real-venue name and likeness

The stadium's name is a naming-rights trademark, and the building's look (the canopy roof, the oval centre board) is recognisable. Using the name, logo or close likeness in a commercial game without a licence from the venue owner risks a trademark or trade-dress claim. US copyright allows pictures of buildings seen from public places, but trademark and trade dress are separate. This is a risk note, not legal advice.

What the pipeline already does:
- `pipeline/venues/stadium_prep.py` **deletes the roof logo object**, gives every part a neutral name (`SM_Stadium_Main_*`), and the venue ships as "Stadium_Main", never by its real name.
- The silhouette is still recognisable. For launch, either (a) license the likeness from the venue, or (b) restyle the canopy and centre board so it reads as an original stadium (cheaper, recommended), or (c) build an original stadium in the style of the reference, as we did for Arena_Main.

## Running the prep

```
uv venv -p 3.11 .bpy && VIRTUAL_ENV=.bpy uv pip install bpy==5.0.1
.bpy/bin/python pipeline/venues/stadium_prep.py --obj "/path/Sofi stadium.obj"
```

Outputs `unreal/SourceArt/Venues/Stadium_Main/SM_Stadium_Main_*.fbx` (Git LFS) plus copied textures and `markers.json` (committed). The field centre is the origin, the field's long axis is X, and the end stage sits past the -X end line, matching every other venue. Verified in the cloud: field 110 x 63 m, logo removed, 17 parts.

## Before it ships in a build

- Seats are one 4.6M-tri mesh (130 MB FBX). Replace with our instanced crowd/seat system using the bowl as the shell, or decimate heavily; it is too heavy for iOS as is.
- Textures are low-res JPGs; re-material with our master materials.
- Add LODs / Nanite on the bowl and canopy.
