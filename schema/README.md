# Show package format, v1

A show package is an **immutable, versioned folder**, stored at `s3://shows/{showId}/v{n}/`.
Editing a show makes a new version; a published version never changes. That keeps live playback
identical on every fan's device.

```
show.json                         manifest            show-package.v1.schema.json
audio/master.ogg                  full mix, 48 kHz
audio/stems/{vocals,drums,bass,other}.ogg
analysis/beats.json               beats, sections     beats.v1.schema.json
motion/body_{performerId}.fbx     shared UE5 Manny skeleton, 30 fps
motion/face_{performerId}.json    ARKit-52 curves, 60 fps
cues/timeline.json                cue tracks          cue-timeline.v1.schema.json
```

## Rules

- **Consent is enforced by the format.** Every performer lists at least one `consentIds` entry
  covering whoever performed the motion and anyone the avatar resembles. No consent, no package.
- **AI disclosure is required.** `rights.aiDisclosure` must be `true`, and `rights.aiTool` records
  which tool and plan produced the track.
- **Cues anchor to music, not clock time, where possible.** Each cue has exactly one anchor:
  `t` (ms), `beat` (index into `beats[]`) or `section` (index into `sections[]`, start or end),
  plus an optional `offsetBeats`. Anchors are resolved to ms at load, so a tempo fix does not
  break the show.
- **Forward compatible.** Unknown track types and extra cue fields are allowed; older clients
  ignore what they do not understand. Known types (`camera`, `lights`, `led`, `pyro`, `crowd`)
  have required params.
- **Paths stay inside the package.** No absolute paths, no `..`.
- **Checksums.** `checksums` maps every file to its sha256 so clients can verify CDN downloads.

The validator in `pipeline/stageverse_schema` checks all of the above plus what JSON Schema cannot:
files exist, checksums match, beats ascend, sections do not overlap, and every cue resolves to a
time inside the show.

## Example

`examples/arizona-rae-demo/` is a placeholder 3-minute, 120 BPM show in the arena. It is generated
by `pipeline/tools/make_example.py`; edit the script, not the JSON. Media files are not
committed, so validate it with `--schema-only`.

## Changing the schema

Additive, optional fields can go into v1. Anything that would make an existing package invalid,
or change how one plays, needs `schemaVersion: 2` and a loader that still reads v1.
