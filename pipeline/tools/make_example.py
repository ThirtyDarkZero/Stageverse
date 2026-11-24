"""Regenerate schema/examples/arizona-rae-demo (manifest, analysis, cues).

The example is a placeholder show for Arizona Rae with a 3-minute, 120 BPM
song. Media files (audio, motion) are not committed, so validate it with
--schema-only. The cue timeline mimics what the auto director will produce.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "schema" / "examples" / "arizona-rae-demo"
DURATION_MS = 180_000
BPM = 120
BEAT = 500  # ms per beat at 120 BPM

beats = list(range(0, DURATION_MS, BEAT))
downbeats = beats[::4]
# (label, start bar, end bar, energy); a bar is 4 beats = 2000 ms
plan = [
    ("intro", 0, 8, 0.25), ("verse", 8, 24, 0.45), ("prechorus", 24, 32, 0.6),
    ("chorus", 32, 48, 0.85), ("verse", 48, 64, 0.5), ("chorus", 64, 80, 0.9),
    ("bridge", 80, 84, 0.4), ("drop", 84, 88, 1.0), ("outro", 88, 90, 0.3),
]
sections = [
    {"label": l, "startMs": s * 2000, "endMs": e * 2000, "energy": en} for l, s, e, en in plan
]

analysis = {
    "schemaVersion": 1,
    "analyzer": "example/handmade",
    "bpm": BPM,
    "beats": beats,
    "downbeats": downbeats,
    "sections": sections,
}

def sec(i, at="start"):
    c = {"section": {"index": i, "label": sections[i]["label"]}}
    if at != "start":
        c["section"]["at"] = at
    return c

shot_for = {"intro": "wide_front", "verse": "mid_front", "prechorus": "close_lead",
            "chorus": "crane_sweep", "bridge": "close_lead", "drop": "wide_front", "outro": "wide_back"}
light_for = {"intro": "blue_wash", "verse": "warm_spot", "prechorus": "build_chase",
             "chorus": "full_rig_white", "bridge": "single_spot", "drop": "strobe_white", "outro": "blue_wash"}
crowd_for = {"intro": "idle", "verse": "sway", "prechorus": "clap", "chorus": "jump",
             "bridge": "phone_lights", "drop": "hands_up", "outro": "cheer"}

cues = {
    "schemaVersion": 1,
    "generatedBy": "example/handmade",
    "tracks": [
        {"type": "camera", "id": "program", "cues": [
            {**sec(i), "shot": shot_for[s["label"]], **({"blendMs": 800} if s["label"] == "chorus" else {})}
            for i, s in enumerate(sections)
        ]},
        {"type": "lights", "id": "main_rig", "cues": [
            {**sec(i), "preset": light_for[s["label"]], "intensity": round(0.4 + 0.6 * s["energy"], 2)}
            for i, s in enumerate(sections)
        ]},
        {"type": "led", "id": "center_board", "cues": [
            {"t": 0, "content": "arizona_rae_logo_loop", "palette": "desert_dusk", "surface": "center_hung"},
            {**sec(3), "content": "audio_reactive_bars", "palette": "desert_dusk", "surface": "center_hung"},
            {**sec(7), "content": "strobe_flash", "palette": "white", "surface": "center_hung"},
        ]},
        {"type": "pyro", "id": "stage_front", "cues": [
            {**sec(3), "effect": "co2_jet", "positions": ["front_l", "front_r"]},
            {**sec(5), "effect": "spark_fountain", "positions": ["front_l", "front_r"]},
            {**sec(7), "offsetBeats": -0.5, "effect": "flame", "positions": ["upstage_l", "upstage_r"]},
            {**sec(8, "end"), "offsetBeats": -2, "effect": "confetti", "positions": ["over_floor"]},
        ]},
        {"type": "crowd", "id": "bowl", "cues": [
            {**sec(i), "state": crowd_for[s["label"]], "intensity": s["energy"]}
            for i, s in enumerate(sections)
        ]},
    ],
}

show = {
    "schemaVersion": 1,
    "showId": "shw_01JDXR4E5V9Q8M7K6H5G4F3E2D",
    "version": 1,
    "title": "Arizona Rae: Demo Show",
    "artistId": "art_01JDXR4E5V9Q8M7K6H5G4F3E2A",
    "durationMs": DURATION_MS,
    "venue": {"tier": "arena", "venueId": "arena_main_01", "stageKit": "kit_end_stage"},
    "act": {"type": "solo", "genre": "pop", "styleTags": ["dance_pop", "rnb"]},
    "audio": {
        "master": "audio/master.ogg",
        "stems": {k: f"audio/stems/{k}.ogg" for k in ("vocals", "drums", "bass", "other")},
        "sampleRate": 48000,
    },
    "analysis": "analysis/beats.json",
    "performers": [{
        "performerId": "arizona_rae",
        "role": "artist",
        "avatarId": "av_01JDXR4E5V9Q8M7K6H5G4F3E2B",
        "consentIds": ["cns_01JDXR4E5V9Q8M7K6H5G4F3E2C"],
        "body": "motion/body_arizona_rae.fbx",
        "face": "motion/face_arizona_rae.json",
        "offsetMs": 0,
        "mark": "center",
        "style": {"dance": "pop", "persona": "diva"},
    }],
    "cues": "cues/timeline.json",
    "rights": {
        "trackLicense": "lic_01JDXR4E5V9Q8M7K6H5G4F3E2E",
        "aiTool": {"name": "TBD", "plan": "TBD"},
        "aiDisclosure": True,
        "rightsAttestedAt": "2026-11-22T00:00:00Z",
    },
    "createdAt": "2026-11-22T00:00:00Z",
}

def dump(rel, obj, compact_lists=False):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2)
    if compact_lists:  # keep the long beat arrays on one line each
        for key in ("beats", "downbeats"):
            text = text.replace(json.dumps(obj[key], indent=2).replace("\n", "\n  "), json.dumps(obj[key]))
    p.write_text(text + "\n")

dump("show.json", show)
dump("analysis/beats.json", analysis, compact_lists=True)
dump("cues/timeline.json", cues)
print(f"wrote example to {ROOT}")
