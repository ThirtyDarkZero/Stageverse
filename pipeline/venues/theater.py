"""Theater_Main: an original ~2,400-capacity concert theater blockout.

In the spirit of a modern downtown LA music theater: a big general-admission
floor stepping up in three terraces, a raked seated balcony at the back with
narrow side galleries along the walls, and a proscenium stage with a full fly
tower. Not a copy of any real building: no names, logos or signage.

Stage is at -X. Everything is symmetric about the X axis.
"""
from __future__ import annotations

import math

import venuekit as vk  # imports bpy first
import bmesh

NAME = "Theater_Main"

GA_DENSITY = 2.5           # standing fans per m^2 (same figure as the arena floor)
SEAT_W, AISLE = 0.5, 0.6

HALL_X0, HALL_X1, HALL_HW, HALL_H = -16.0, 20.0, 14.0, 15.0     # audience hall
HOUSE_X0, HOUSE_HW, FLY_H = -30.0, 16.0, 24.0                    # stage house + fly tower
DECK_H, APRON_X = 1.3, -14.0
PROS_HW, PROS_H = 7.5, 8.5                                        # proscenium opening 15 x 8.5 m
BARRICADE_X = -12.5
TERRACES = [(-14.0, 6.0, 0.0), (6.0, 11.0, 0.45), (11.0, HALL_X1, 0.9)]  # (x0, x1, z)
BAL_X, BAL_HW, BAL_Z, BAL_ROWS, BAL_DEPTH = 8.0, 11.0, 5.2, 9, 0.9
GAL_X0, GAL_X1, GAL_Y, GAL_ROWS = -10.0, 7.5, 10.0, 3
FOH = (12.5, 0.0, 5.0, 3.5)  # x, y, width (Y), depth (X)
WALL_T = 0.5


def build():
    v = vk.Venue(NAME, "Theater (original design, ~2,400 GA + balcony)",
                 notes="Greybox layout blockout. Dress with the Concert Arena Stage kit and theater "
                       "props; keep these markers and seat points as the source of truth.")

    # ---- floor terraces + rails --------------------------------------------
    bm = bmesh.new()
    for x0, x1, z in TERRACES:
        vk.add_box(bm, ((x0 + x1) / 2, 0, (z - 0.4) / 2), (x1 - x0, 2 * HALL_HW, z + 0.4), 0, 0)
    vk.make_object(v.part("Floor"), f"SM_{NAME}_Floor", bm, ["M_GB_Floor"])

    bm = bmesh.new()
    for x0, _, z in TERRACES[1:]:  # rails along each terrace edge, with 3 m gaps for flow
        for y0, y1 in ((-HALL_HW + 1.0, -1.5), (1.5, HALL_HW - 1.0)):
            vk.add_box(bm, (x0, (y0 + y1) / 2, z + 0.55), (0.08, y1 - y0, 1.1), 0, 0)
    for y0, y1 in ((-11.5, -1.5), (1.5, 11.5)):  # front barricade (1.5 m pit), centre gap for security
        vk.add_box(bm, (BARRICADE_X, (y0 + y1) / 2, 0.6), (0.12, y1 - y0, 1.2), 0, 0)
    fx, fy, fw, fd = FOH
    ft = TERRACES[2][2] if fx > TERRACES[2][0] else TERRACES[1][2]
    vk.add_box(bm, (fx, fy, ft + 0.15), (fd, fw, 0.3), 0, 1)
    vk.make_object(v.part("FloorProduction"), f"SM_{NAME}_FloorProduction", bm,
                   ["M_GB_Barricade", "M_GB_StageDeck"])

    # ---- bars ------------------------------------------------------------
    bm = bmesh.new()
    vk.add_box(bm, (HALL_X1 - 1.0, 0, TERRACES[2][2] + 0.55), (1.0, 14.0, 1.1), 0, 0)
    for sgn in (-1, 1):
        vk.add_box(bm, (2.0, sgn * (HALL_HW - 0.9), 0.55), (8.0, 0.9, 1.1), 0, 0)
    vk.make_object(v.part("Bars"), f"SM_{NAME}_Bars", bm, ["M_GB_Bar"])
    bars = [(HALL_X1 - 1.0, 0, 14.0 + 1.0, 1.0 + 1.0), (2.0, HALL_HW - 0.9, 8.0 + 1.0, 0.9 + 1.0),
            (2.0, -(HALL_HW - 0.9), 8.0 + 1.0, 0.9 + 1.0)]  # x, y, len (Y or X), depth incl. queue

    # ---- stage, apron, proscenium, fly tower -------------------------------
    bm = bmesh.new()
    vk.add_box(bm, ((HOUSE_X0 + 1 + HALL_X0) / 2, 0, DECK_H / 2), (HALL_X0 - HOUSE_X0 - 1, 2 * HOUSE_HW - 1, DECK_H), 0, 0)
    apron = [(HALL_X0, -PROS_HW - 1.5), (APRON_X + 0.6, -PROS_HW), (APRON_X, -4.0), (APRON_X, 4.0),
             (APRON_X + 0.6, PROS_HW), (HALL_X0, PROS_HW + 1.5)]
    vk.add_prism(bm, apron, 0.0, DECK_H, 0)
    vk.make_object(v.part("Stage_Main"), f"SM_{NAME}_Stage_Main", bm, ["M_GB_StageDeck"])

    bm = bmesh.new()
    t = 1.0  # proscenium wall thickness
    side_w = HOUSE_HW - PROS_HW
    for sgn in (-1, 1):
        vk.add_box(bm, (HALL_X0 - t / 2, sgn * (PROS_HW + side_w / 2), FLY_H / 2), (t, side_w, FLY_H), 0, 0)
    head_z0 = DECK_H + PROS_H
    vk.add_box(bm, (HALL_X0 - t / 2, 0, (head_z0 + FLY_H) / 2), (t, 2 * PROS_HW, FLY_H - head_z0), 0, 0)
    vk.add_box(bm, (HALL_X0 - t / 2, 0, DECK_H / 2), (t, 2 * PROS_HW, DECK_H), 0, 0)
    # stage house walls
    for sgn in (-1, 1):
        vk.add_box(bm, ((HOUSE_X0 + HALL_X0 - t) / 2, sgn * (HOUSE_HW + WALL_T / 2), FLY_H / 2),
                   (HALL_X0 - t - HOUSE_X0, WALL_T, FLY_H), 0, 0)
    vk.add_box(bm, (HOUSE_X0 - WALL_T / 2, 0, FLY_H / 2), (WALL_T, 2 * HOUSE_HW + 2 * WALL_T, FLY_H), 0, 0)
    vk.make_object(v.part("StageHouse"), f"SM_{NAME}_StageHouse", bm, ["M_GB_Wall"])

    bm = bmesh.new()  # house curtain (open, gathered at the sides) + masking legs + upstage LED
    for sgn in (-1, 1):
        vk.add_box(bm, (HALL_X0 - 1.3, sgn * (PROS_HW - 0.9), DECK_H + PROS_H / 2), (0.15, 1.8, PROS_H), 0, 0)
        for k, x in enumerate((-19.5, -23.0, -26.5)):
            vk.add_box(bm, (x, sgn * (PROS_HW + 0.2 + 0.3 * k), DECK_H + 4.5), (0.1, 2.4, 9.0), 0, 0)
    vk.add_box(bm, (HOUSE_X0 + 1.2, 0, DECK_H + 0.3 + 3.5), (0.25, 13.0, 7.0), 0, 1)
    vk.make_object(v.part("Stage_Drapes"), f"SM_{NAME}_Stage_Drapes", bm, ["M_GB_Curtain", "M_GB_LED"])

    # ---- audience hall shell -----------------------------------------------
    bm = bmesh.new()
    for sgn in (-1, 1):
        vk.add_box(bm, ((HALL_X0 + HALL_X1) / 2, sgn * (HALL_HW + WALL_T / 2), HALL_H / 2),
                   (HALL_X1 - HALL_X0, WALL_T, HALL_H + 0.8), 0, 0)
    vk.add_box(bm, (HALL_X1 + WALL_T / 2, 0, HALL_H / 2), (WALL_T, 2 * HALL_HW + 2 * WALL_T, HALL_H + 0.8), 0, 0)
    vk.make_object(v.part("HallWalls"), f"SM_{NAME}_HallWalls", bm, ["M_GB_Wall"])

    bm = bmesh.new()
    vk.add_box(bm, ((HALL_X0 + HALL_X1) / 2, 0, HALL_H + 0.4), (HALL_X1 - HALL_X0, 2 * HALL_HW + 1, 0.8), 0, 0)
    vk.add_box(bm, ((HOUSE_X0 + HALL_X0) / 2, 0, FLY_H + 0.4), (HALL_X0 - HOUSE_X0 + 0.5, 2 * HOUSE_HW + 1, 0.8), 0, 0)
    vk.make_object(v.part("Roof"), f"SM_{NAME}_Roof", bm, ["M_GB_Roof"])

    # ---- balcony + side galleries -------------------------------------------
    sections = []
    back = vk.LinePath((BAL_X, -BAL_HW), (BAL_X, BAL_HW), (1, 0))
    bal = vk.Tier("Balcony", d0=0.0, z0=BAL_Z, rows=BAL_ROWS, row_depth=BAL_DEPTH, rise_first=0.42,
                  rise_last=0.55, front_wall=1.0, underside_drop=1.2)
    bm = bmesh.new()
    vk.loft_section(bm, back, 0.0, 1.0, bal.profile(), 0, step=2.0)
    # balcony lobby slab from the cross aisle to the back wall
    vk.add_box(bm, ((BAL_X + bal.d_end + 1.2 + HALL_X1) / 2, 0, bal.top_z - 0.3),
               (HALL_X1 - BAL_X - bal.d_end - 1.2, 2 * HALL_HW, 0.6), 0, 0)
    vk.make_object(v.part("Balcony"), f"SM_{NAME}_Balcony", bm, ["M_GB_SeatBalcony"])
    for sid, t0, t1 in (("BAL_R", 0.0, 0.3), ("BAL_C", 0.3, 0.7), ("BAL_L", 0.7, 1.0)):
        sections.append(("balcony", sid, back, bal, t0, t1, 180.0))

    gal = vk.Tier("Gallery", d0=0.0, z0=BAL_Z, rows=GAL_ROWS, row_depth=BAL_DEPTH, rise_first=0.45,
                  rise_last=0.5, front_wall=1.0, underside_drop=1.0)
    bm = bmesh.new()
    for sgn, side in ((1, "L"), (-1, "R")):
        p = vk.LinePath((GAL_X0, sgn * GAL_Y), (GAL_X1, sgn * GAL_Y), (0, sgn))
        vk.loft_section(bm, p, 0.0, 1.0, gal.profile(), 0, step=2.0)
        sections.append(("gallery", f"GAL_{side}1", p, gal, 0.0, 0.5, None))
        sections.append(("gallery", f"GAL_{side}2", p, gal, 0.5, 1.0, None))
    vk.make_object(v.part("Galleries"), f"SM_{NAME}_Galleries", bm, ["M_GB_SeatBalcony"])

    stage_c = (-21.0, 0.0)
    seat_count = {"balcony": 0, "gallery": 0}
    for tier_name, sid, p, tier, t0, t1, _ in sections:
        seats = []
        for r in range(tier.rows):
            d = tier.d_front(r) + 0.55
            z = tier.rows_z[r] + 0.45
            for t, xy in vk.points_along(p, t0, t1, d, SEAT_W, AISLE):
                yaw = math.degrees(math.atan2(stage_c[1] - xy.y, stage_c[0] - xy.x))
                view = 1 if (tier_name == "gallery" and abs(xy.y) > 10 and xy.x < -6) else 0
                seats.append((xy.x, xy.y, z, yaw, r + 1, view))
        seat_count[tier_name] += len(seats)
        v.add_section(sid, tier_name, seats, sold_end_stage=True,
                      standing=tier_name == "gallery", path_range=[t0, t1])

    # ---- floor GA standing points ------------------------------------------
    sp = 1.0 / math.sqrt(GA_DENSITY)
    ga = {"FLOOR_FRONT": [], "FLOOR_MID": [], "FLOOR_REAR": []}

    def blocked(x, y):
        if abs(x - fx) < fd / 2 + 1.0 and abs(y - fy) < fw / 2 + 1.0:
            return True
        for bx, by, bl, bd in bars:
            if by == 0 and abs(x - bx) < bd / 2 + 0.5 and abs(y) < bl / 2:
                return True
            if by != 0 and abs(x - bx) < bl / 2 and abs(y - by) < bd / 2 + 0.5:
                return True
        return False

    for (x0, x1, z), key in zip(TERRACES, ga):
        x = max(x0, BARRICADE_X + 0.4) + sp / 2
        while x < x1 - 0.2:
            y = -HALL_HW + 0.4
            while y <= HALL_HW - 0.4:
                if not blocked(x, y):
                    ga[key].append((x, y, z, 180.0, 0, 0))
                y += sp
            x += sp
    for sid, pts in ga.items():
        v.add_section(sid, "floor_ga", pts, standing=True, density_per_m2=GA_DENSITY, sold_end_stage=True)
    ga_total = sum(len(p) for p in ga.values())
    v.capacity.update({
        "floor_ga_standing": ga_total,
        "balcony_seats": seat_count["balcony"],
        "gallery_spots": seat_count["gallery"],
        "total": ga_total + seat_count["balcony"] + seat_count["gallery"],
        "ga_density_per_m2": GA_DENSITY,
    })

    # ---- zones and marks -----------------------------------------------
    v.zone("stage_zone", "Zone_MainDeck", ((HALL_X0 + HOUSE_X0 + 1) / 2, 0, DECK_H), (HALL_X0 - HOUSE_X0 - 1, 2 * PROS_HW, 0))
    v.zone("stage_zone", "Zone_Apron", ((APRON_X + HALL_X0) / 2, 0, DECK_H), (HALL_X0 - APRON_X, 2 * PROS_HW, 0))
    v.zone("stage_zone", "Zone_Wing_SL", (-23.0, PROS_HW + (HOUSE_HW - PROS_HW) / 2, DECK_H), (12.0, HOUSE_HW - PROS_HW, 0))
    v.zone("stage_zone", "Zone_Wing_SR", (-23.0, -PROS_HW - (HOUSE_HW - PROS_HW) / 2, DECK_H), (12.0, HOUSE_HW - PROS_HW, 0))
    v.zone("stage_zone", "Zone_Proscenium", (HALL_X0 - 0.5, 0, DECK_H + PROS_H / 2), (1.0, 2 * PROS_HW, PROS_H))
    v.zone("stage_zone", "Zone_LEDWall", (HOUSE_X0 + 1.2, 0, DECK_H + 0.3 + 3.5), (0.25, 13.0, 7.0))
    v.zone("crowd_zone", "Zone_Pit", ((BARRICADE_X + APRON_X) / 2, 0, 0), (1.5, 23.0, 2.0), note="security only")
    v.zone("crowd_zone", "Zone_FOH", (fx, fy, ft + 0.3), (fd, fw, 3.0))
    for (x0, x1, z), key in zip(TERRACES, ga):
        x0 = max(x0, BARRICADE_X)
        v.zone("crowd_zone", f"Zone_{key.title().replace('_', '')}", ((x0 + x1) / 2, 0, z), (x1 - x0, 2 * HALL_HW, 2.0),
               section=key)
    for bx, by, bl, bd in bars:
        size = (bd, bl, 1.1) if by == 0 else (bl, bd, 1.1)
        v.zone("bar", f"Bar_{'Back' if by == 0 else ('SL' if by > 0 else 'SR')}", (bx, by, 0), size)

    for mid, x in (("Mark_Upstage", -26.0), ("Mark_Center", -21.0), ("Mark_Downstage", -17.0), ("Mark_Apron", -15.0)):
        v.marker("performer_mark", mid, (x, 0, DECK_H), 0.0)
    for sgn, side in ((1, "SL"), (-1, "SR")):
        v.marker("performer_mark", f"Mark_Dancer_{side}1", (-20.0, sgn * 3.5, DECK_H), 0.0)
        v.marker("performer_mark", f"Mark_Dancer_{side}2", (-23.0, sgn * 5.5, DECK_H), 0.0)
        v.marker("performer_mark", f"Mark_Entrance_{side}", (-21.0, sgn * (PROS_HW + 1.5), DECK_H), -90.0 * sgn)

    # ---- rigging ----------------------------------------------------------
    grid_z = FLY_H - 2.0
    k = 0
    x = HALL_X0 - 1.6
    while x > HOUSE_X0 + 1.5:
        k += 1
        v.marker("rig_lineset", f"LS_{k:02d}", (x, 0, grid_z), batten_m=18.0, max_out_trim_m=grid_z - 1,
                 load_kg=500)
        x -= 0.3
    bm = bmesh.new()  # FOH truss over the floor + a few battens drawn for reference
    vk.add_box(bm, (-8.0, 0, 10.0), (0.4, 20.0, 0.4), 0, 0)
    for x in (-17.5, -21.0, -25.0):
        vk.add_box(bm, (x, 0, DECK_H + PROS_H + 0.5), (0.1, 18.0, 0.1), 0, 0)
    vk.make_object(v.part("Rigging"), f"SM_{NAME}_Rigging", bm, ["M_GB_Steel"])
    for y in (-9.0, 0.0, 9.0):
        v.marker("rig_point", f"Rig_FOHTruss_{'SR' if y < 0 else 'SL' if y > 0 else 'C'}", (-8.0, y, HALL_H - 0.2),
                 load_kg=750, trim_m=10.0)
    for sgn, side in ((1, "SL"), (-1, "SR")):
        v.marker("rig_point", f"Rig_PA_{side}", (HALL_X0 + 1.0, sgn * 9.8, HALL_H - 0.2), load_kg=1200, trim_m=9.0)
        v.marker("rig_point", f"Rig_BoxBoom_{side}", (-12.0, sgn * (HALL_HW - 0.3), 7.0), 0.0, load_kg=150)
        v.marker("rig_point", f"Rig_DelayPA_{side}", (BAL_X - 0.5, sgn * 8.0, HALL_H - 0.2), load_kg=400, trim_m=7.5)
    v.marker("rig_point", "Rig_BalconyRail", (BAL_X, 0, BAL_Z + 1.0), 180.0, length_m=2 * BAL_HW)
    for sgn in (1, -1):
        s = "SL" if sgn > 0 else "SR"
        v.marker("fx_point", f"FX_Pyro_DS_{s}", (APRON_X + 0.4, sgn * 5.5, DECK_H), 0.0, note="cold spark only (indoor theater)")
        v.marker("fx_point", f"FX_CO2_{s}", (HALL_X0 - 0.8, sgn * (PROS_HW - 0.5), DECK_H), 0.0)
        v.marker("fx_point", f"FX_Confetti_{s}", (-8.0, sgn * 6.0, 10.0), 0.0)
    v.marker("fx_point", "FX_Haze_US", (HOUSE_X0 + 2, 0, DECK_H), 0.0)

    # ---- cameras -----------------------------------------------------------
    st = (-21.0, 0, DECK_H + 1.7)
    v.look_at("camera", "Cam_Balcony_Centre", (BAL_X + bal.d_front(5), 0, bal.rows_z[5] + 1.6), st, lens_mm=85)
    v.look_at("camera", "Cam_Balcony_Wide", (BAL_X + bal.d_front(8), 3.0, bal.rows_z[8] + 1.6), st, lens_mm=24)
    v.look_at("camera", "Cam_FOH", (fx - 2.5, 0.5, ft + 1.8), st, lens_mm=50)
    v.look_at("camera", "Cam_Pit_Dolly_Start", (BARRICADE_X - 0.7, -9.0, 1.4), (-20.0, 0, DECK_H + 1.6), lens_mm=24,
              track_end_m=[BARRICADE_X - 0.7, 9.0, 1.4])
    for sgn, side in ((1, "SL"), (-1, "SR")):
        v.look_at("camera", f"Cam_Wing_{side}", (-19.0, sgn * (PROS_HW + 0.8), DECK_H + 1.6), (-15.0, -sgn * 2, DECK_H + 1.6),
                  lens_mm=24, handheld=True)
        v.look_at("camera", f"Cam_Gallery_{side}", (-4.0, sgn * (GAL_Y + 1.5), BAL_Z + 1.8), st, lens_mm=50)
    v.look_at("camera", "Cam_CrowdPOV", (-4.0, 2.0, 1.65), st, lens_mm=18, note="fan eye height")
    v.look_at("camera", "Cam_Overhead", (-10.0, 0, 14.0), (-18.0, 0, DECK_H), lens_mm=18)
    return v, {}


VIEWS = {
    "aerial": ((40, -42, 38), (-8, 0, 3), 28, None, ("Roof", "HallWalls")),
    "balcony": ((BAL_X + 7.5, 0, BAL_Z + 5.0), (-21, 0, 4.5), 20, None),
    "floor": ((-4.0, 2.0, 1.65), (-21, 0, 4), 20, None),
    "plan": ((-5, 0, 120), (-5, 0, 0), None, 58, ("Roof", "HallWalls")),
}
HIDE_IN_PREVIEW = ("Roof",)
