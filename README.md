# StageVerse

A game where AI artists perform live shows, built in Unreal Engine.

**Core idea:** a show is data. An artist's track, motion, avatar, stage and cues are packed into a
*show package*, and every fan's device renders that package live in sync.

Phase 1 (the MVP, ~12 weeks) delivers one original concert arena, an auto-generated show, and
multi-camera video export, demoed with our launch artist **Arizona Rae**.

## Repository layout

| Folder | What lives there |
| --- | --- |
| `schema/` | The show package format: JSON Schemas and an example package. The contract every other part builds against. |
| `pipeline/` | Python: show package validator now; cloud GPU stages (stems, beats, mocap, lip sync) next. |
| `unreal/` | The Unreal Engine 5.6 project (`StageVerse.uproject`) and its plugins. Assets use Git LFS. |
| `web/` | Next.js app and API: accounts, uploads, consent, show library, job status. |
| `docs/` | Architecture notes and decisions. |

## Quick start (schema and pipeline)

```bash
cd pipeline
pip install -e ".[dev]"
pytest -q
python -m stageverse_schema validate ../schema/examples/arizona-rae-demo --schema-only
```

## Engine

We use the stock Unreal Engine 5.6 from the Epic Games Launcher for Phase 1. A source build is only
needed later for dedicated servers, and must come from Epic's official `EpicGames/UnrealEngine`
repository (requires linking an Epic account to GitHub). Do not vendor or build from unofficial
copies of engine source.

## Git LFS

Install Git LFS before cloning (`git lfs install`). Binary assets (`.uasset`, `.umap`, `.fbx`,
audio, video, images) are tracked by LFS through `.gitattributes`.
