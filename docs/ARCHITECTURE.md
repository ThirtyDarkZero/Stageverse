# Architecture (Phase 1)

The full engineering plan, timeline and risk list live in the project's plan doc. Summary:

1. **Uploads** (web): track, avatar (FBX / GLB / VRM), performance video, consent records.
2. **Cloud GPU pipeline** (`pipeline/`): stems (Demucs), beats and sections, body mocap
   (GVHMR / WHAM) retargeted to the UE5 Manny skeleton, face and lip sync from the vocal stem
   (Audio2Face-3D). Each stage writes one part of the show package.
3. **Show package** (`schema/`): the contract between everything.
4. **Unreal** (`unreal/`): plays the package against an audio-driven clock; the auto director
   writes the cue timeline; Movie Render Queue exports a program cut plus ISO cameras.
5. **Backend** (`web/`): Next.js + Postgres + S3/CloudFront, with a Postgres-backed job queue.

Team: Rob (Unreal editor, arena, art, Arizona Rae content) and Claude (code).

Milestone gates: week 4, a hand-built package plays in the arena blockout; week 8, upload to
show with no manual steps; week 12, three Arizona Rae songs exported as multi-cam video.
