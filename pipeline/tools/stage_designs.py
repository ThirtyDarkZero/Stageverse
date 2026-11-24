"""Generate the StageVerse stage-design catalogue: 3 original stage kits per venue tier.

Writes, for each design:
  content/stages/<tier>/<stageKit>.json   validated by schema/stage-design.v1.schema.json
  content/stages/<tier>/<stageKit>.svg    top-down plan in the brand street palette
and content/stages/index.json for the Show Producer / Studio stage picker.

Edit this script, not the generated files. Run from the repo root:
    python pipeline/tools/stage_designs.py

Frame: metres, Z up, stage at -X, audience toward +X, symmetric about X, the same frame
as each venue's markers.json (unreal/SourceArt/Venues/<Venue>/markers.json).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "content" / "stages"

# Brand street palette (approved 2026-11-24)
BLACKOUT, CONCRETE, PAPER, RED, ICE, BLUE = "#080808", "#141414", "#F1EEE8", "#FF1F2E", "#A8E8FF", "#2E6BFF"

# --------------------------------------------------------------------------------------
# Venues: outline used for the plan drawing plus the facts the picker shows.
# --------------------------------------------------------------------------------------
VENUES = {
    "club_main_01": {
        "tier": "club", "name": "Club (original)", "capacity": 800,
        "blockout": None,  # no blockout yet; dims below are the design envelope
        "outline": [("rect", -14, -10, 28, 20)],
        "floor": ("rect", -9, -10, 23, 20),
        "ceiling_m": 5.0,
        "view": (-16, -12, 32, 24),
    },
    "theater_main_01": {
        "tier": "theater", "name": "Theater_Main", "capacity": 2379,
        "blockout": "unreal/SourceArt/Venues/Theater_Main",
        "outline": [("rect", -16, -14, 38, 28), ("rect", -30, -16, 14, 32)],
        "floor": ("rect", -12.5, -14, 34.5, 28),
        "ceiling_m": 22.0,
        "view": (-32, -18, 56, 36),
    },
    "arena_main_01": {
        "tier": "arena", "name": "Arena_Main", "capacity": 18652,
        "blockout": "unreal/SourceArt/Venues/Arena_Main",
        "outline": [("ellipse", 0, 0, 48, 38), ("ellipse", 0, 0, 34, 22)],
        "floor": ("rect", -12.5, -15, 43, 30),
        "ceiling_m": 31.0,
        "view": (-50, -40, 100, 80),
    },
    "stadium_main_01": {
        "tier": "stadium", "name": "Stadium_Main (de-branded, from the stadium model)", "capacity": 70000,
        "blockout": None,  # Stadium_Main import pending licence check; see docs/venues/stadium_main.md
        "outline": [("ellipse", 0, 0, 100, 80), ("ellipse", 0, 0, 78, 52)],
        "floor": ("rect", -55, -24.4, 110, 48.8),
        "ceiling_m": 55.0,
        "view": (-80, -64, 145, 128),
    },
}

# --------------------------------------------------------------------------------------
# Element helpers. x,y = centre; w along X (depth toward audience), d along Y (width).
# --------------------------------------------------------------------------------------
def rect(id, kind, x, y, w, d, z=0.0, h=0.0, **kw):
    return {"id": id, "kind": kind, "shape": "rect", "x": x, "y": y, "w": w, "d": d, "z": z, "h": h, **kw}


def disc(id, kind, x, y, r, z=0.0, h=0.0, **kw):
    return {"id": id, "kind": kind, "shape": "disc", "x": x, "y": y, "r": r, "z": z, "h": h, **kw}


def ring(id, kind, x, y, r, width, z=0.0, h=0.0, **kw):
    return {"id": id, "kind": kind, "shape": "ring", "x": x, "y": y, "r": r, "width": width, "z": z, "h": h, **kw}


def mark(id, x, y, z):
    return {"id": id, "x": x, "y": y, "z": z}


def fx(id, x, y, z, effects):
    return {"id": id, "x": x, "y": y, "z": z, "effects": effects}


def act(name, when, state, light):
    return {"name": name, "when": when, "state": state, "light": light}


# --------------------------------------------------------------------------------------
# The designs
# --------------------------------------------------------------------------------------
DESIGNS = []

# ---------------- CLUB ----------------------------------------------------------------
DESIGNS.append({
    "stageKit": "club_low_ceiling", "name": "Low Ceiling", "venueId": "club_main_01",
    "shape": "end_stage",
    "concept": "The ceiling is the instrument: a grid of light batons breathes, presses down on the crowd, then lets go.",
    "object": "48 kinetic pixel batons hung in a 6 x 8 grid over the whole room",
    "photoMoment": "The batons dropped to just above raised hands, all red, the artist on the crowd riser with the grid sloping toward her.",
    "palette": [BLACKOUT, ICE, RED, PAPER],
    "elements": [
        rect("deck_main", "deck", -11.5, 0, 5, 10, z=1.0),
        rect("riser_crowd", "deck", -6.5, 0, 2, 2, z=0.6, note="Low riser in the crowd, reached by steps off the deck."),
        rect("baton_grid", "kinetic", 0, 0, 20, 16, z=4.2, h=0.1, travel_m=[2.6, 4.4],
             note="48 batons, 6 rows (X) x 8 columns (Y), each 2.4 m pixel tube on its own winch. Moves as waves."),
        rect("led_back", "led_surface", -13.9, 0, 0.2, 6, z=1.0, h=3.0, note="Small, low upstage strip; texture only."),
        rect("fixtures_floor", "fixture_array", -9.4, 0, 0.4, 9, z=1.0, note="8 floor wash/beam fixtures along the deck edge, uplighting the batons."),
    ],
    "marks": [mark("center", -11.5, 0, 1.0), mark("downstage", -9.6, 0, 1.0), mark("crowd_riser", -6.5, 0, 0.6)],
    "cueTargets": {
        "ledSurfaces": ["led_back"], "lightGroups": ["batons", "floor_uplight", "key_front", "strobe_room"],
        "pyroPositions": ["co2_sl", "co2_sr", "confetti_center"], "kinetics": ["baton_grid"],
    },
    "fx": [fx("co2_sl", -9.5, 4.5, 1.0, ["co2_jet"]), fx("co2_sr", -9.5, -4.5, 1.0, ["co2_jet"]),
           fx("confetti_center", 0, 0, 4.6, ["confetti"])],
    "acts": [
        act("Hum", "intro and first verse", "Batons flat at 4.4 m, barely glowing.", "Ice blue, key light only on the artist."),
        act("Breathing", "choruses", "Batons ripple in waves from the stage to the back wall, one row per beat.", "Ice with paper-white peaks on the downbeat."),
        act("Pressure", "bridge into the last drop", "Batons drop to 2.6 m and tilt toward the stage; the artist moves to the crowd riser.", "Riot red, room strobes on the snare."),
        act("Release", "final chorus", "Batons snap back to 4.4 m; CO2 and confetti.", "Full paper white, then blackout on the last word."),
    ],
    "buildNotes": "Ceiling 5 m, so batons never go below 2.6 m over the floor. In-game: 48 instanced meshes, one material instance, wave motion driven by a curve on the cue clock. No flames indoors.",
})

DESIGNS.append({
    "stageKit": "club_tunnel", "name": "Tunnel", "venueId": "club_main_01",
    "shape": "end_stage",
    "concept": "A corridor of light frames pulls the eye to one point; the artist is always at the end of the tunnel.",
    "object": "7 square portal frames edged in LED, receding from over the crowd to upstage",
    "photoMoment": "All seven frames chasing toward the artist in white, shot from the back of the room down the tunnel.",
    "palette": [BLACKOUT, PAPER, RED],
    "elements": [
        rect("deck_main", "deck", -11.5, 0, 5, 10, z=1.0),
        *[rect(f"portal_{i+1}", "kinetic", -13.0 + i * 3.0, 0, 0.3, 9.0 - i * 0.0, z=0.0, h=4.6,
               note="Square frame, LED edge both faces. Frames 1-3 over the deck, 4-7 over the crowd at 4.6 m clear.")
          for i in range(7)],
        rect("haze_floor", "fx_zone", -9.0, 0, 2, 10, note="Low fog along the deck edge."),
    ],
    "marks": [mark("center", -12.0, 0, 1.0), mark("downstage", -9.6, 0, 1.0)],
    "cueTargets": {
        "ledSurfaces": [f"portal_{i+1}" for i in range(7)],
        "lightGroups": ["portal_edges", "key_front", "backlight", "strobe_room"],
        "pyroPositions": ["co2_sl", "co2_sr", "fog_ds"], "kinetics": ["portal_1", "portal_2", "portal_3"],
    },
    "fx": [fx("co2_sl", -9.5, 4.5, 1.0, ["co2_jet"]), fx("co2_sr", -9.5, -4.5, 1.0, ["co2_jet"]),
           fx("fog_ds", -9.0, 0, 1.0, ["fog"])],
    "acts": [
        act("Silhouette", "intro", "Only the upstage frame lit, artist backlit inside it.", "One paper-white backlight, everything else black."),
        act("Chase", "verses and choruses", "Frames chase on the beat toward the stage (back of room first).", "Paper white, red on the downbeat of each bar."),
        act("Collapse", "breakdown", "The three stage frames tilt off-axis (10 degrees) so the tunnel breaks.", "Red only, low fog."),
        act("Run-out", "final chorus", "Frames re-align and strobe in sequence; CO2 on the last hit.", "Full white, blackout on the last word."),
    ],
    "buildNotes": "Frames 4-7 hang over the crowd, so they must clear 4.6 m (ceiling 5 m). Frames 1-3 tilt on two hoists each. In-game: one frame mesh, emissive edge material with a per-instance chase offset.",
})

DESIGNS.append({
    "stageKit": "club_cage", "name": "Cage", "venueId": "club_main_01",
    "shape": "in_the_round",
    "concept": "The artist starts locked in a cage of light in the middle of the crowd and breaks it open.",
    "object": "A 4 x 4 m riser in the centre of the floor wrapped by 64 vertical light tubes that rise from the floor",
    "photoMoment": "The tubes dropping into the floor in one sweep while the crowd closes in around the riser.",
    "palette": [BLACKOUT, RED, ICE],
    "elements": [
        rect("riser_center", "deck", 0, 0, 4, 4, z=0.8, note="Crowd on all four sides."),
        ring("cage_tubes", "kinetic", 0, 0, 3.0, 0.3, z=0.0, h=4.0, travel_m=[0.0, 4.0],
             note="64 pixel tubes on a 6 x 6 m square footprint (16 per side), rising out of floor pods."),
        rect("booth_dj", "deck", -11.5, 0, 5, 8, z=1.0, note="Main deck becomes the DJ / band booth."),
        rect("led_back", "led_surface", -13.9, 0, 0.2, 8, z=1.0, h=3.0),
        rect("grid_over", "truss", 0, 0, 6, 6, z=4.6, note="Square truss over the riser: key lights and 4 beams."),
    ],
    "marks": [mark("center", 0, 0, 0.8), mark("riser_sl", 0, 1.5, 0.8), mark("riser_sr", 0, -1.5, 0.8),
              mark("booth", -11.5, 0, 1.0)],
    "cueTargets": {
        "ledSurfaces": ["led_back"], "lightGroups": ["cage_tubes", "over_key", "over_beams", "strobe_room"],
        "pyroPositions": ["co2_ne", "co2_nw", "co2_se", "co2_sw"], "kinetics": ["cage_tubes"],
    },
    "fx": [fx("co2_ne", 3, 3, 0, ["co2_jet"]), fx("co2_nw", -3, 3, 0, ["co2_jet"]),
           fx("co2_se", 3, -3, 0, ["co2_jet"]), fx("co2_sw", -3, -3, 0, ["co2_jet"])],
    "acts": [
        act("Locked", "intro and verse", "Tubes fully up at 4 m, artist inside.", "Red tubes, cold ice key from above."),
        act("Bars", "choruses", "Tubes chase around the square; single tubes drop and return on hits.", "Red and ice alternating per bar."),
        act("Break-out", "the drop", "All 64 tubes drop into the floor in one sweep; crowd closes in.", "Blackout for one beat, then white beams from the truss."),
        act("Rave", "final chorus", "Tubes pulse at floor height like a lit floor edge; CO2 from the four corners.", "Strobes and ice, end on a red flash."),
    ],
    "buildNotes": "Needs a central security ring of 1 m. In-game: tubes are instanced; the riser blocks crowd spawn in a 7 x 7 m square at the floor centre.",
})

# ---------------- THEATER --------------------------------------------------------------
DESIGNS.append({
    "stageKit": "theater_false_frame", "name": "False Frame", "venueId": "theater_main_01",
    "shape": "proscenium",
    "concept": "A picture frame inside the picture frame: the artist starts as a portrait, then the frame breaks and the room opens up.",
    "object": "An LED-edged inner portal plus a flown ceiling 'lid' that tilts down over the stage",
    "photoMoment": "The lid tilted down to head height in red, the artist pressed under it at centre.",
    "palette": [BLACKOUT, PAPER, RED],
    "elements": [
        rect("deck_main", "deck", -22.5, 0, 13, 15, z=1.3, finish="black mirror"),
        rect("portal_inner", "kinetic", -18.0, 0, 0.4, 11, z=1.3, h=6.5, note="LED edge frame on lineset LS_02. Flies out."),
        rect("lid", "kinetic", -22.5, 0, 8, 12, z=9.0, h=0.2, travel_m=[3.0, 12.0], tilt_deg=[0, 90],
             note="12 x 8 m panel on 4 linesets (LS_10, LS_14, LS_18, LS_22). LED underside. Ends vertical as the backdrop."),
        rect("led_wall", "led_surface", -28.8, 0, 0.25, 13, z=1.3, h=7.0),
        rect("apron", "deck", -15.0, 0, 2, 15, z=1.3),
    ],
    "marks": [mark("center", -21.0, 0, 1.3), mark("portrait", -18.8, 0, 1.3), mark("apron", -15.0, 0, 1.3),
              mark("upstage", -26.0, 0, 1.3)],
    "cueTargets": {
        "ledSurfaces": ["portal_inner", "lid", "led_wall"],
        "lightGroups": ["portal_edge", "lid_under", "key_front", "side_light", "backlight"],
        "pyroPositions": ["spark_sl", "spark_sr", "confetti_house"], "kinetics": ["portal_inner", "lid"],
    },
    "fx": [fx("spark_sl", -13.6, 5.5, 1.3, ["spark_fountain"]), fx("spark_sr", -13.6, -5.5, 1.3, ["spark_fountain"]),
           fx("confetti_house", -8.0, 0, 10.0, ["confetti"])],
    "acts": [
        act("Portrait", "intro and verse", "Inner frame in, everything else dark; the artist stands in the frame.", "Paper-white frame edge, soft key."),
        act("The Lid", "second verse into bridge", "Lid tilts down to 3 m over centre stage.", "Red under-lid, hard side light."),
        act("Break", "the drop", "Frame flies out, lid swings to vertical and becomes the backdrop; full depth revealed.", "Blackout one beat, then full white backlight."),
        act("Open", "final chorus", "Lid and LED wall play as one surface; cold sparks downstage.", "White and red, confetti on the last chorus."),
    ],
    "buildNotes": "Lid weight about 1.6 t on 4 sets (500 kg each). Cold spark only (indoor theater). In-game: lid is one mesh with an LED material; pivot along its upstage edge.",
})

DESIGNS.append({
    "stageKit": "theater_staircase", "name": "Staircase", "venueId": "theater_main_01",
    "shape": "proscenium",
    "concept": "One monumental white stair: the show is an entrance, a descent, a seat and an exit.",
    "object": "A 10 m wide stair rising 5 m to a doorway upstage, every riser an LED strip",
    "photoMoment": "The artist in silhouette in the doorway at the top of the stair, every riser lit white below her.",
    "palette": [PAPER, BLACKOUT, ICE],
    "elements": [
        rect("deck_main", "deck", -22.5, 0, 13, 15, z=1.3),
        rect("stair", "structure", -23.0, 0, 8, 10, z=1.3, h=5.0, steps=20,
             note="20 risers of 25 cm, 40 cm treads; LED strip in each riser; treads take projection."),
        rect("landing_door", "structure", -27.6, 0, 1.2, 3, z=6.3, h=3.2, note="Doorway at the top with a white backlight behind."),
        rect("scrim_sl", "scrim", -21.0, 6.5, 8, 0.1, z=1.3, h=8.0),
        rect("scrim_sr", "scrim", -21.0, -6.5, 8, 0.1, z=1.3, h=8.0),
    ],
    "marks": [mark("door", -27.6, 0, 6.3), mark("stair_mid", -23.0, 0, 3.8), mark("center", -18.6, 0, 1.3),
              mark("downstage", -17.0, 0, 1.3)],
    "cueTargets": {
        "ledSurfaces": ["stair_risers", "stair_treads"],
        "lightGroups": ["door_backlight", "risers", "key_front", "side_light", "follow_spot"],
        "pyroPositions": ["confetti_house", "haze_us"], "kinetics": [],
    },
    "fx": [fx("confetti_house", -8.0, 0, 10.0, ["confetti"]), fx("haze_us", -28.0, 0, 1.3, ["fog"])],
    "acts": [
        act("Entrance", "intro", "Artist appears in the doorway, backlit, and holds.", "Single white backlight through haze, stair dark."),
        act("Descent", "verse and chorus", "Artist walks down; risers light one step per beat beneath her.", "White risers, ice side light."),
        act("Seated", "ballad / bridge", "Artist sits on the stair; treads show slow projected texture.", "One follow spot, everything else off."),
        act("Exit", "final chorus and outro", "Artist climbs back up into the white door; confetti over the house.", "Full white, door flares, blackout."),
    ],
    "buildNotes": "Stair is a static set piece (no kinetics), so it is the cheapest design to build first. Rail-free stair: keep choreography slow on it.",
})

DESIGNS.append({
    "stageKit": "theater_curtain_machine", "name": "Curtain Machine", "venueId": "theater_main_01",
    "shape": "proscenium",
    "concept": "Five veils between the artist and the crowd are stripped away one chorus at a time until nothing is left.",
    "object": "Five projection gauzes on traveller tracks plus a red drop curtain",
    "photoMoment": "The red drop falling at the final chorus, revealing the artist in a white field.",
    "palette": [BLACKOUT, RED, PAPER],
    "elements": [
        rect("deck_main", "deck", -22.5, 0, 13, 15, z=1.3),
        *[rect(f"gauze_{i+1}", "scrim", x, 0, 0.1, 15, z=1.3, h=8.0, lineset=ls,
               note="Projection gauze, splits as two travellers or flies out.")
          for i, (x, ls) in enumerate([(-17.6, "LS_01"), (-19.4, "LS_07"), (-21.2, "LS_13"), (-23.0, "LS_19"), (-24.8, "LS_25")])],
        rect("drop_red", "kinetic", -26.6, 0, 0.1, 15, z=1.3, h=8.5, lineset="LS_31", note="Kabuki drop: falls in one cue."),
        rect("led_wall", "led_surface", -28.8, 0, 0.25, 13, z=1.3, h=7.0),
        rect("projector_foh", "fixture_array", 8.0, 0, 1, 4, z=6.2, note="Projectors on the balcony rail."),
    ],
    "marks": [mark("behind_veils", -25.5, 0, 1.3), mark("center", -21.0, 0, 1.3), mark("downstage", -17.0, 0, 1.3)],
    "cueTargets": {
        "ledSurfaces": ["led_wall", "gauze_projection"],
        "lightGroups": ["backlight", "key_front", "side_light", "follow_spot"],
        "pyroPositions": ["spark_sl", "spark_sr", "haze_us"], "kinetics": ["gauze_1", "gauze_2", "gauze_3", "gauze_4", "gauze_5", "drop_red"],
    },
    "fx": [fx("spark_sl", -13.6, 5.5, 1.3, ["spark_fountain"]), fx("spark_sr", -13.6, -5.5, 1.3, ["spark_fountain"]),
           fx("haze_us", -28.0, 0, 1.3, ["fog"])],
    "acts": [
        act("Veils", "intro", "All five gauzes in; artist behind them as layered silhouettes.", "Backlight only, projected text on gauze 1."),
        act("Peel", "each chorus", "One gauze goes per chorus (travels off or flies out).", "Each layer gets one colour; red reaches the front last."),
        act("Void", "bridge", "No gauze left: black box, one follow spot.", "Follow spot only."),
        act("Kabuki", "final chorus", "Red drop falls, LED wall behind goes full white; cold sparks.", "White and red, blackout on the last word."),
    ],
    "buildNotes": "Gauzes render as translucent masked planes with a projection decal; keep layer count at 5 for overdraw. Cold spark only.",
})

# ---------------- ARENA ----------------------------------------------------------------
DESIGNS.append({
    "stageKit": "arena_halo", "name": "Halo", "venueId": "arena_main_01",
    "shape": "end_stage_runway_bstage",
    "concept": "A ring of light hangs over the crowd like a promise; the whole show is the artist's walk to stand inside it.",
    "object": "A 24 m kinetic ring of light that tilts, lowers and rains sparks over the B-stage",
    "photoMoment": "The ring lowered around the artist on the raised B-stage, spark rain falling from it on every side.",
    "palette": [BLACKOUT, PAPER, ICE, RED],
    "elements": [
        rect("deck_main", "deck", -21.25, 0, 14.5, 22, z=1.8, finish="black mirror"),
        rect("runway", "deck", -6.75, 0, 14.5, 3, z=1.8),
        disc("bstage", "deck", 5.0, 0, 4.5, z=1.8),
        disc("bstage_lift", "lift", 5.0, 0, 1.5, z=1.8, travel_m=[0.0, 3.0]),
        ring("halo", "kinetic", 5.0, 0, 12.0, 1.2, z=24.0, travel_m=[8.0, 24.0], tilt_deg=[0, 20],
             note="Ring truss with an LED band inside and outside and 48 beam fixtures; 4 hoists."),
        rect("void_wall", "scrim", -28.1, 0, 0.3, 20, z=1.8, h=10, note="Black scrim replacing the LED wall."),
        rect("slot", "led_surface", -28.0, 0, 0.3, 2, z=1.8, h=10, note="One 2 x 10 m vertical LED slot, the only screen upstage."),
        rect("imag_sl", "led_surface", -23.25, 16.5, 0.3, 6, z=4.0, h=10, note="Portrait IMAG screen."),
        rect("imag_sr", "led_surface", -23.25, -16.5, 0.3, 6, z=4.0, h=10, note="Portrait IMAG screen."),
    ],
    "marks": [mark("upstage", -24.5, 0, 1.8), mark("center", -19.25, 0, 1.8), mark("downstage", -15.5, 0, 1.8),
              mark("runway_mid", -6.75, 0, 1.8), mark("bstage", 5.0, 0, 1.8)],
    "cueTargets": {
        "ledSurfaces": ["slot", "halo_band", "imag_sl", "imag_sr"],
        "lightGroups": ["halo_beams", "halo_band", "floor_uplight", "key_front", "audience_blinders"],
        "pyroPositions": ["halo_rain", "co2_runway_sl", "co2_runway_sr", "confetti_floor"], "kinetics": ["halo", "bstage_lift"],
    },
    "fx": [fx("halo_rain", 5.0, 0, 8.0, ["spark_fountain"]), fx("co2_runway_sl", -6.75, 2.0, 1.8, ["co2_jet"]),
           fx("co2_runway_sr", -6.75, -2.0, 1.8, ["co2_jet"]), fx("confetti_floor", 5.0, 0, 26.0, ["confetti", "streamer"])],
    "acts": [
        act("Descent", "opener", "Halo flat at 24 m, dark; only the upstage slot lit, artist appears in it.", "White slot, everything else black."),
        act("Pressure", "songs 2-3", "Halo tilts 15 degrees toward the stage and pulses with the kick.", "Ice band, red beams on choruses."),
        act("Walk", "the runway song", "Artist walks the runway; halo lowers to 8 m around the B-stage.", "Follow spot and blinders on the crowd."),
        act("Inside", "closer", "Lift raises the artist into the ring; spark rain falls from it; confetti.", "Full white, then a single red ring on the last word."),
    ],
    "buildNotes": "The centre-hung board is hidden for this kit and the halo hangs from the grid over the B-stage (4 x 1 t points). In-game: ring is 1 mesh plus 48 instanced fixtures; spark rain is one Niagara system.",
})

DESIGNS.append({
    "stageKit": "arena_fault_line", "name": "Fault Line", "venueId": "arena_main_01",
    "shape": "end_stage_runway_bstage",
    "concept": "The stage is solid ground that cracks open: light pours out of the fractures and the runway is the crack.",
    "object": "A fractured stage floor of tilting LED plates and three leaning monolith screens",
    "photoMoment": "The artist on a plate tilted 12 degrees, red light pouring up through the crack beside her, flames along the runway.",
    "palette": [BLACKOUT, CONCRETE, RED, ICE],
    "elements": [
        *[rect(f"plate_{i+1}", "kinetic", x, y, 6.5, 7.0, z=1.8, tilt_deg=[0, 12], note="LED floor plate on 2 actuators.")
          for i, (x, y) in enumerate([(-24.5, 7.0), (-24.5, -7.0), (-17.5, 7.5), (-17.5, -7.5), (-21.0, 0.0)])],
        rect("crack", "led_surface", -6.75, 0, 14.5, 1.0, z=1.6, note="LED trench down the runway centreline."),
        rect("runway", "deck", -6.75, 0, 14.5, 3, z=1.8),
        disc("bstage", "deck", 5.0, 0, 4.5, z=1.8),
        rect("mono_c", "kinetic", -28.0, 0, 0.4, 8, z=1.8, h=12, tilt_deg=[-10, 10]),
        rect("mono_sl", "kinetic", -27.0, 8.5, 0.4, 6, z=1.8, h=14, tilt_deg=[-10, 10]),
        rect("mono_sr", "kinetic", -27.0, -8.5, 0.4, 6, z=1.8, h=14, tilt_deg=[-10, 10]),
    ],
    "marks": [mark("center", -21.0, 0, 1.8), mark("plate_sl", -17.5, 7.5, 1.8), mark("plate_sr", -17.5, -7.5, 1.8),
              mark("runway_mid", -6.75, 0, 1.8), mark("bstage", 5.0, 0, 1.8)],
    "cueTargets": {
        "ledSurfaces": ["plates", "crack", "mono_c", "mono_sl", "mono_sr"],
        "lightGroups": ["crack_uplight", "key_front", "side_beams", "audience_blinders", "lasers"],
        "pyroPositions": ["flame_runway_1", "flame_runway_2", "flame_runway_3", "flame_runway_4", "co2_ds_sl", "co2_ds_sr"],
        "kinetics": ["plate_1", "plate_2", "plate_3", "plate_4", "plate_5", "mono_c", "mono_sl", "mono_sr"],
    },
    "fx": [*[fx(f"flame_runway_{i+1}", -13.0 + i * 4.0, s * 1.8, 1.8, ["flame"]) for i, s in enumerate([1, -1, 1, -1])],
           fx("co2_ds_sl", -14.5, 9.0, 1.8, ["co2_jet"]), fx("co2_ds_sr", -14.5, -9.0, 1.8, ["co2_jet"])],
    "acts": [
        act("Plate", "opener", "Plates flat and the three monoliths aligned as one wall.", "Cold ice texture like stone, white key."),
        act("Rupture", "first big drop", "Monoliths split and lean apart; plates tilt out of level.", "Red light up through every gap, lasers through the cracks."),
        act("Crossing", "runway song", "Artist walks the crack to the B-stage; trench chases under her.", "Red trench, ice on the crowd."),
        act("Eruption", "closer", "All plates at 12 degrees; flames along the runway on each downbeat.", "Full red, white blinders on the final hit."),
    ],
    "buildNotes": "Tilt max 12 degrees for performer safety. Flames are outdoor-rated in real life; acceptable in the arena kit with 6 m clearance. In-game: plates share one material; crack glow is an emissive panel plus lights.",
})

DESIGNS.append({
    "stageKit": "arena_satellite", "name": "Satellite", "venueId": "arena_main_01",
    "shape": "in_the_round",
    "concept": "A broadcast tower in the middle of the room sends the artist out to every side of the bowl.",
    "object": "An overhead inverted cube of four LED faces that separate, drop and open like petals",
    "photoMoment": "The cube faces open outward like petals at 6 m, lasers fanning from each corner to the upper bowl.",
    "palette": [BLACKOUT, BLUE, ICE, PAPER],
    "elements": [
        rect("deck_center", "deck", 0, 0, 14, 14, z=1.8),
        disc("turntable", "turntable", 0, 0, 4.0, z=1.8),
        disc("center_lift", "lift", 0, 0, 1.5, z=1.8, travel_m=[-2.0, 3.0]),
        *[rect(f"spoke_{n}", "deck", x, y, w, d, z=1.2) for n, x, y, w, d in
          [("e", 13.0, 0, 12, 2.5), ("w", -13.0, 0, 12, 2.5), ("n", 0, 12.0, 2.5, 10), ("s", 0, -12.0, 2.5, 10)]],
        *[disc(f"satellite_{n}", "deck", x, y, 2.5, z=1.2) for n, x, y in [("e", 20.5, 0), ("w", -20.5, 0), ("n", 0, 18.5), ("s", 0, -18.5)]],
        *[rect(f"cube_{n}", "kinetic", x, y, w, d, z=14.0, h=7.0, travel_m=[6.0, 14.0], tilt_deg=[0, 45]) for n, x, y, w, d in
          [("e", 6.0, 0, 0.3, 12), ("w", -6.0, 0, 0.3, 12), ("n", 0, 6.0, 12, 0.3), ("s", 0, -6.0, 12, 0.3)]],
    ],
    "marks": [mark("center", 0, 0, 1.8), mark("sat_e", 20.5, 0, 1.2), mark("sat_w", -20.5, 0, 1.2),
              mark("sat_n", 0, 18.5, 1.2), mark("sat_s", 0, -18.5, 1.2)],
    "cueTargets": {
        "ledSurfaces": ["cube_e", "cube_w", "cube_n", "cube_s", "deck_edge"],
        "lightGroups": ["cube_inner", "corner_lasers", "key_360", "audience_blinders"],
        "pyroPositions": ["co2_ne", "co2_nw", "co2_se", "co2_sw", "confetti_center"],
        "kinetics": ["cube_e", "cube_w", "cube_n", "cube_s", "turntable", "center_lift"],
    },
    "fx": [fx("co2_ne", 7, 7, 1.8, ["co2_jet"]), fx("co2_nw", -7, 7, 1.8, ["co2_jet"]),
           fx("co2_se", 7, -7, 1.8, ["co2_jet"]), fx("co2_sw", -7, -7, 1.8, ["co2_jet"]),
           fx("confetti_center", 0, 0, 22.0, ["confetti"])],
    "acts": [
        act("Signal", "opener", "Cube closed at 14 m; artist rises on the centre lift inside its light.", "Blue cube, single white key from above."),
        act("Broadcast", "songs 2-4", "Faces separate outward and show four-way IMAG; turntable rotates slowly.", "Ice and blue, lasers on choruses."),
        act("Satellites", "middle section", "Artist visits each satellite stage; one face follows as a screen for that side.", "Key 360 on the artist, blinders per side."),
        act("Petals", "closer", "Cube drops to 6 m and the faces tilt 45 degrees open; lasers fan from the corners.", "Full white and blue, confetti."),
    ],
    "buildNotes": "In-the-round uses the full bowl (about 22,260). Centre-hung board hidden. Crowd spawn must avoid spokes and satellites. In-game: 4 face meshes, turntable rotates the deck mesh only.",
})

# ---------------- STADIUM --------------------------------------------------------------
DESIGNS.append({
    "stageKit": "stadium_horizon", "name": "Horizon", "venueId": "stadium_main_01",
    "shape": "end_stage_runway_bstage",
    "concept": "A city skyline of light the artist builds one tower at a time, then walks away from to meet the crowd.",
    "object": "Nine LED columns of different heights forming an 80 m skyline",
    "photoMoment": "Fireworks bursting off the tops of all nine columns while the artist stands alone on the midfield stage.",
    "palette": [BLACKOUT, PAPER, RED, ICE],
    "elements": [
        rect("deck_main", "deck", -63.0, 0, 18, 60, z=2.5),
        *[rect(f"column_{i+1}", "led_surface", -71.0, y, 2.0, wdt, z=2.5, h=hgt)
          for i, (y, wdt, hgt) in enumerate([(-36, 6, 14), (-27, 6, 20), (-18, 8, 26), (-9, 6, 18), (0, 8, 32),
                                             (9, 6, 18), (18, 8, 26), (27, 6, 20), (36, 6, 14)])],
        rect("runway", "deck", -27.0, 0, 54, 4, z=2.0),
        disc("bstage", "deck", 8.0, 0, 8.0, z=2.0),
        disc("bstage_lift", "lift", 8.0, 0, 2.0, z=2.0, travel_m=[0.0, 4.0]),
        rect("imag_sl", "led_surface", -60.0, 44.0, 1, 12, z=8.0, h=20, note="IMAG framed as the outermost towers."),
        rect("imag_sr", "led_surface", -60.0, -44.0, 1, 12, z=8.0, h=20),
        rect("tower_sl", "truss", 30.0, 30.0, 3, 3, z=0.0, h=18, note="Delay / follow-spot tower."),
        rect("tower_sr", "truss", 30.0, -30.0, 3, 3, z=0.0, h=18, note="Delay / follow-spot tower."),
    ],
    "marks": [mark("center", -60.0, 0, 2.5), mark("downstage", -55.0, 0, 2.5), mark("runway_mid", -27.0, 0, 2.0),
              mark("bstage", 8.0, 0, 2.0)],
    "cueTargets": {
        "ledSurfaces": [f"column_{i+1}" for i in range(9)] + ["imag_sl", "imag_sr"],
        "lightGroups": ["column_tops", "key_front", "runway_edges", "stadium_blinders", "lasers"],
        "pyroPositions": [f"firework_{i+1}" for i in range(9)] + ["flame_runway_sl", "flame_runway_sr"],
        "kinetics": ["bstage_lift"],
    },
    "fx": [*[fx(f"firework_{i+1}", -71.0, y, 2.5 + hgt, ["spark_fountain"]) for i, (y, hgt) in
             enumerate([(-36, 14), (-27, 20), (-18, 26), (-9, 18), (0, 32), (9, 18), (18, 26), (27, 20), (36, 14)])],
           fx("flame_runway_sl", -27.0, 3.0, 2.0, ["flame"]), fx("flame_runway_sr", -27.0, -3.0, 2.0, ["flame"])],
    "acts": [
        act("Dawn", "opener (daylight if open-air)", "Columns dark; the artist walks out in plain light.", "No colour, just white key and sun."),
        act("City", "songs 2-5", "Columns light one at a time, building the skyline song by song.", "Paper white windows, red on the tallest column."),
        act("Long Walk", "runway song", "Artist walks 54 m to the midfield stage; flame bars along the runway on the beat.", "Ice runway edges, follow spots from the delay towers."),
        act("Skyline", "closer", "Lift raises the artist at midfield; fireworks from every column top.", "Full white, then red on the last hit."),
    ],
    "buildNotes": "Upstage of the end line (stage frame: field ends at x = -55). Fireworks only for open-air or retractable roof; with the roof closed swap to spark fountains. In-game: columns are scaled instances of one LED box.",
})

DESIGNS.append({
    "stageKit": "stadium_orbit", "name": "Orbit", "venueId": "stadium_main_01",
    "shape": "in_the_round",
    "concept": "The artist is the centre of gravity: a stage at midfield with everything, including the crowd, in orbit around her.",
    "object": "A 40 m floating ring of light held by four towers over a circular stage and a ring runway",
    "photoMoment": "The ring lowered and tilted over the artist, lasers from all four towers meeting above her head.",
    "palette": [BLACKOUT, ICE, BLUE, PAPER],
    "elements": [
        disc("deck_center", "deck", 0, 0, 12.0, z=2.0),
        disc("turntable", "turntable", 0, 0, 5.0, z=2.0),
        ring("ring_runway", "deck", 0, 0, 22.0, 4.0, z=1.6),
        *[rect(f"bridge_{n}", "deck", x, y, w, d, z=1.8) for n, x, y, w, d in
          [("e", 16.0, 0, 8, 3), ("w", -16.0, 0, 8, 3), ("n", 0, 16.0, 3, 8), ("s", 0, -16.0, 3, 8)]],
        *[rect(f"tower_{n}", "truss", x, y, 4, 4, z=0, h=40) for n, x, y in [("ne", 30, 30), ("nw", -30, 30), ("se", 30, -30), ("sw", -30, -30)]],
        ring("orbit_ring", "kinetic", 0, 0, 20.0, 2.0, z=30.0, travel_m=[12.0, 32.0], tilt_deg=[0, 25],
             note="LED ring held on a cable net between the four towers."),
    ],
    "marks": [mark("center", 0, 0, 2.0), mark("ring_e", 22, 0, 1.6), mark("ring_w", -22, 0, 1.6),
              mark("ring_n", 0, 22, 1.6), mark("ring_s", 0, -22, 1.6)],
    "cueTargets": {
        "ledSurfaces": ["orbit_ring", "deck_edge", "tower_imag"],
        "lightGroups": ["tower_lasers", "ring_beams", "key_360", "stadium_blinders"],
        "pyroPositions": ["flame_ne", "flame_nw", "flame_se", "flame_sw", "confetti_ring"],
        "kinetics": ["orbit_ring", "turntable"],
    },
    "fx": [*[fx(f"flame_{n}", x, y, 40.0, ["flame"]) for n, x, y in [("ne", 30, 30), ("nw", -30, 30), ("se", 30, -30), ("sw", -30, -30)]],
           fx("confetti_ring", 0, 0, 30.0, ["confetti", "streamer"])],
    "acts": [
        act("Eclipse", "opener", "Ring high and dark; one white beam on the artist from directly above.", "Black stadium, single beam."),
        act("Rotation", "songs 2-5", "Turntable spins slowly; ring chases around in time with the bar.", "Ice and blue."),
        act("Orbit", "middle section", "Artist walks the ring runway past every section of the floor.", "Key 360, blinders sweep with her."),
        act("Gravity", "closer", "Ring lowers to 12 m and tilts; lasers from the four towers meet over the stage; flames on top of the towers.", "Full white, confetti from the ring."),
    ],
    "buildNotes": "Centre stage blocks about 2,000 floor spots; seats all the way round. Towers placed outside the field width so floor sightlines stay clear. In-game: ring is one mesh; cable net is decorative splines.",
})

DESIGNS.append({
    "stageKit": "stadium_monument", "name": "Monument", "venueId": "stadium_main_01",
    "shape": "end_stage_thrust",
    "concept": "A sealed 30 m monolith stands at the end of the field; the show is about getting it to open.",
    "object": "A split black monolith whose two halves slide apart to reveal the artist on a lift inside",
    "photoMoment": "The halves parting on the drop, white light bursting through the gap, the artist 10 m up on the lift inside.",
    "palette": [BLACKOUT, PAPER, RED],
    "elements": [
        rect("deck_main", "deck", -62.0, 0, 16, 44, z=2.5),
        rect("mono_left", "kinetic", -70.0, 6.5, 6, 13, z=2.5, h=30, travel_m=[0.0, 10.0],
             note="Half monolith on tracks; slides stage-left up to 10 m. Projection-mapped outside, LED inside face."),
        rect("mono_right", "kinetic", -70.0, -6.5, 6, 13, z=2.5, h=30, travel_m=[0.0, 10.0]),
        rect("inner_led", "led_surface", -72.5, 0, 0.5, 8, z=2.5, h=28),
        rect("inner_lift", "lift", -70.0, 0, 3, 3, z=2.5, travel_m=[0.0, 10.0]),
        rect("thrust", "deck", -42.0, 0, 30, 10, z=2.0),
        rect("imag_sl", "led_surface", -64.0, 30.0, 1, 10, z=6.0, h=18),
        rect("imag_sr", "led_surface", -64.0, -30.0, 1, 10, z=6.0, h=18),
    ],
    "marks": [mark("lift", -70.0, 0, 2.5), mark("center", -60.0, 0, 2.5), mark("thrust_end", -28.0, 0, 2.0)],
    "cueTargets": {
        "ledSurfaces": ["inner_led", "mono_outer_projection", "imag_sl", "imag_sr"],
        "lightGroups": ["seam_light", "key_front", "thrust_edges", "stadium_blinders"],
        "pyroPositions": ["mono_top_sl", "mono_top_sr", "flame_thrust_sl", "flame_thrust_sr"],
        "kinetics": ["mono_left", "mono_right", "inner_lift"],
    },
    "fx": [fx("mono_top_sl", -70.0, 6.5, 32.5, ["flame", "spark_fountain"]), fx("mono_top_sr", -70.0, -6.5, 32.5, ["flame", "spark_fountain"]),
           fx("flame_thrust_sl", -35.0, 5.5, 2.0, ["flame"]), fx("flame_thrust_sr", -35.0, -5.5, 2.0, ["flame"])],
    "acts": [
        act("Sealed", "opener", "Monolith closed; slow projected texture over its skin; artist on the thrust in front of it.", "Low white, IMAG only."),
        act("Seam", "songs 2-4", "Light leaks through a thin open seam, a little wider each song.", "White seam, red key."),
        act("Open", "the big drop", "Halves slide 10 m apart; the artist is revealed rising on the inner lift.", "Blinding white from inside, blinders on the crowd."),
        act("Inside", "closer", "Inner LED and outer projection play together; flames from the monolith tops.", "Red and white, blackout on the last hit."),
    ],
    "buildNotes": "Each half is about 30 x 13 x 6 m. Wind load would make this unrealistic outdoors; fine in-game. In-game: two meshes with a projection decal outside and an LED material inside.",
})

# --------------------------------------------------------------------------------------
# SVG plan
# --------------------------------------------------------------------------------------
KIND_STYLE = {
    "deck": dict(fill=CONCRETE, stroke=PAPER, sw=1.2),
    "lift": dict(fill="none", stroke=RED, sw=1.4, dash="4 3"),
    "turntable": dict(fill="none", stroke=PAPER, sw=1.0, dash="2 3"),
    "led_surface": dict(fill=ICE, stroke=ICE, sw=1.0, op=0.85),
    "kinetic": dict(fill="none", stroke=RED, sw=2.0),
    "truss": dict(fill="none", stroke=PAPER, sw=0.8, dash="1 2"),
    "structure": dict(fill=PAPER, stroke=PAPER, sw=1.0, op=0.35),
    "scrim": dict(fill="none", stroke=BLUE, sw=1.6),
    "fixture_array": dict(fill="none", stroke=ICE, sw=0.8, dash="1 1"),
    "fx_zone": dict(fill="none", stroke=PAPER, sw=0.6, dash="1 3"),
}


def svg_plan(d: dict) -> str:
    v = VENUES[d["venueId"]]
    vx, vy, vw, vh = v["view"]
    W, H, pad, head = 1200, 860, 40, 110
    # Stage at the top: venue X (toward audience) runs down the page, venue Y (stage left) runs right.
    s = min((W - 2 * pad) / vh, (H - head - pad - 60) / vw)
    ox = pad + ((W - 2 * pad) - vh * s) / 2
    oy = head + ((H - head - pad - 60) - vw * s) / 2

    def P(x, y):
        return ox + (y - vy) * s, oy + (x - vx) * s

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
           f'<rect width="{W}" height="{H}" fill="{BLACKOUT}"/>',
           '<style>text{font-family:"Space Mono","JetBrains Mono",monospace;fill:%s}'
           '.h{font-family:Anton,"Big Shoulders Display",Impact,sans-serif;font-size:52px;letter-spacing:1px}'
           '.s{font-size:15px}.l{font-size:11px;opacity:.8}</style>' % PAPER]
    out.append(f'<text class="h" x="{pad}" y="62">{d["name"].upper()}</text>')
    out.append(f'<text class="s" x="{pad}" y="90" fill="{RED}" style="fill:{RED}">{v["tier"].upper()} · {d["shape"].replace("_", " ").upper()} · {d["stageKit"]}</text>')

    # venue outline
    for o in v["outline"]:
        if o[0] == "rect":
            _, x, y, w, dd = o
            x0, y0 = P(x, y)
            out.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{dd * s:.1f}" height="{w * s:.1f}" fill="none" stroke="{PAPER}" stroke-opacity=".25" stroke-width="1"/>')
        else:
            _, cx, cy, rx, ry = o
            px, py = P(cx, cy)
            out.append(f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="{ry * s:.1f}" ry="{rx * s:.1f}" fill="none" stroke="{PAPER}" stroke-opacity=".25" stroke-width="1"/>')
    _, fx_, fy, fw, fd = v["floor"]
    x0, y0 = P(fx_, fy)
    out.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{fd * s:.1f}" height="{fw * s:.1f}" fill="{PAPER}" fill-opacity=".04" stroke="none"/>')

    order = ["structure", "deck", "turntable", "lift", "scrim", "led_surface", "fixture_array", "truss", "fx_zone", "kinetic"]
    for e in sorted(d["elements"], key=lambda e: order.index(e["kind"])):
        st = KIND_STYLE[e["kind"]]
        attrs = f'fill="{st["fill"]}" stroke="{st["stroke"]}" stroke-width="{st["sw"]}"'
        if "dash" in st:
            attrs += f' stroke-dasharray="{st["dash"]}"'
        if "op" in st:
            attrs += f' fill-opacity="{st["op"]}"'
        if e["shape"] == "rect":
            x0, y0 = P(e["x"] - e["w"] / 2, e["y"] - e["d"] / 2)
            out.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{max(e["d"] * s, 2):.1f}" height="{max(e["w"] * s, 2):.1f}" {attrs}/>')
        elif e["shape"] == "disc":
            px, py = P(e["x"], e["y"])
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{e["r"] * s:.1f}" {attrs}/>')
        else:
            px, py = P(e["x"], e["y"])
            if e["id"] == "cage_tubes":
                half = 3.0 * s
                out.append(f'<rect x="{px - half:.1f}" y="{py - half:.1f}" width="{2 * half:.1f}" height="{2 * half:.1f}" fill="none" stroke="{RED}" stroke-width="{max(e["width"] * s, 2):.1f}" stroke-dasharray="3 3"/>')
            else:
                out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{e["r"] * s:.1f}" fill="none" stroke="{st["stroke"]}" stroke-width="{max(e["width"] * s, 2):.1f}" stroke-opacity=".9"/>')
    for f in d["fx"]:
        px, py = P(f["x"], f["y"])
        out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{RED}"/>')
    for m in d["marks"]:
        px, py = P(m["x"], m["y"])
        out.append(f'<path d="M{px - 5:.1f} {py:.1f}h10M{px:.1f} {py - 5:.1f}v10" stroke="{PAPER}" stroke-width="1.6"/>')

    # scale bar + legend
    bar = 10 if v["tier"] in ("club", "theater") else (20 if v["tier"] == "arena" else 50)
    y = H - 30
    out.append(f'<path d="M{pad} {y}h{bar * s:.1f}" stroke="{PAPER}" stroke-width="2"/><text class="l" x="{pad}" y="{y - 8}">{bar} m</text>')
    legend = [("deck", CONCRETE, PAPER), ("LED", ICE, ICE), ("kinetic", "none", RED), ("scrim", "none", BLUE), ("FX", RED, RED)]
    lx = pad + bar * s + 40
    for name, fill, stroke in legend:
        out.append(f'<rect x="{lx:.1f}" y="{y - 12}" width="14" height="10" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/><text class="l" x="{lx + 20:.1f}" y="{y - 3}">{name}</text>')
        lx += 90
    out.append(f'<text class="l" x="{lx:.1f}" y="{y - 3}">+ performer mark · stage at top, audience below</text>')
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------------------
def main() -> None:
    index = {"schemaVersion": 1, "generatedBy": "pipeline/tools/stage_designs.py", "venues": [], "designs": []}
    for vid, v in VENUES.items():
        index["venues"].append({"venueId": vid, "tier": v["tier"], "name": v["name"], "capacity": v["capacity"],
                                "blockout": v["blockout"], "stageKits": [d["stageKit"] for d in DESIGNS if d["venueId"] == vid]})
    for d in DESIGNS:
        v = VENUES[d["venueId"]]
        doc = {"schemaVersion": 1, "tier": v["tier"], **d}
        folder = OUT / v["tier"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f'{d["stageKit"]}.json').write_text(json.dumps(doc, indent=2) + "\n")
        (folder / f'{d["stageKit"]}.svg').write_text(svg_plan(doc) + "\n")
        index["designs"].append({"stageKit": d["stageKit"], "name": d["name"], "tier": v["tier"], "venueId": d["venueId"],
                                 "shape": d["shape"], "concept": d["concept"], "palette": d["palette"],
                                 "spec": f'{v["tier"]}/{d["stageKit"]}.json', "plan": f'{v["tier"]}/{d["stageKit"]}.svg'})
    (OUT / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(f"wrote {len(DESIGNS)} designs to {OUT}")


if __name__ == "__main__":
    main()
