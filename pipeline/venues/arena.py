"""Arena_Main: an original ~19k concert arena blockout (end-stage configuration).

In the spirit of a modern downtown NBA/NHL arena: oval two-tier bowl, a ring of
suites between the tiers, centre-hung video board, flat roof with a rigging
grid. It is not a copy of any real building: no names, logos, signage or
signature rooflines. Dimensions follow common arena design practice:
hockey-size event floor (61 x 30 m, 8.5 m corners), 0.85 m lower rows with a
rising riser (C-value curve), steeper 0.80 m upper rows, ~32 m to roof steel.

Stage is at -X. Everything is symmetric about the X axis.
"""
from __future__ import annotations

import math

import venuekit as vk  # imports bpy first
import bmesh

NAME = "Arena_Main"

# ---- core dimensions (meters) ---------------------------------------------
FLOOR_L, FLOOR_W, FLOOR_R = 61.0, 30.0, 8.5
SEAT_W = 0.50               # seat pitch along a row
AISLE = 0.60                # half-aisle kept clear at each section edge
GA_DENSITY = 2.5            # standing fans per m^2 on the floor (typical concert GA design figure)

LOWER = dict(d0=1.5, z0=0.9, rows=22, row_depth=0.85, rise_first=0.30, rise_last=0.50, front_wall=1.1)
SUITE_DEPTH, SUITE_H, SUITE_W = 6.0, 3.6, 4.2
UPPER_ROWS, UPPER_DEPTH = 20, 0.80
OUTER_WALL_GAP = 1.8        # concourse depth behind the upper cross aisle
ROOF_STEEL_Z = 31.0         # bottom chord of the roof trusses (rig grid height)

# ---- stage (end stage at -X) ---------------------------------------------
DECK_H = 1.8
DECK_BACK_X, DECK_FRONT_X, DECK_W = -28.5, -14.0, 22.0
RUNWAY_END_X, RUNWAY_W = 0.5, 3.0
BSTAGE_X, BSTAGE_R = 5.0, 4.5
BARRICADE_X = -12.5          # 1.5 m pit in front of the deck
FOH_X, FOH_SIZE = 18.0, (8.0, 6.0)
KILL_X = -27.5               # seats behind this line are not sold end-stage
LIMITED_X = -19.0            # seats between KILL_X and here are side/limited view

# 20 sections per tier: east end 2, each corner 2, each long side 4, west end 2
SECTION_SPLITS = {0: 2, 1: 2, 2: 4, 3: 2, 4: 2, 5: 2, 6: 4, 7: 2}


def section_ranges():
    out = []
    for seg in range(8):
        n = SECTION_SPLITS[seg]
        for k in range(n):
            out.append((seg + k / n, seg + (k + 1) / n))
    return out


def seat_view(x):
    if x < KILL_X:
        return 2
    if x < LIMITED_X:
        return 1
    return 0


def build():
    v = vk.Venue(NAME, "Arena (original design, ~19k end-stage concert)",
                 notes="Greybox layout blockout. Dress with the Fab International Arena shell and the "
                       "Concert Arena Stage kit; keep these markers and seat points as the source of truth.")
    path = vk.RoundedRect(FLOOR_L, FLOOR_W, FLOOR_R)
    lower = vk.Tier("Lower", **LOWER)
    suite_d0 = lower.d_end + 1.2
    suite_d1 = suite_d0 + SUITE_DEPTH
    suite_z = lower.top_z
    upper = vk.Tier("Upper", d0=suite_d0 + 2.6, z0=suite_z + SUITE_H + 2.2, rows=UPPER_ROWS,
                    row_depth=UPPER_DEPTH, rise_first=0.52, rise_last=0.64, front_wall=1.1,
                    underside_drop=1.6)
    outer_d = upper.d_end + 1.2 + OUTER_WALL_GAP
    roof_z = max(ROOF_STEEL_Z + 2.0, upper.top_z + 6.0)

    # ---- event floor -------------------------------------------------------
    bm = bmesh.new()
    vk.add_prism(bm, vk.rounded_rect_poly(path, LOWER["d0"]), -0.4, 0.0, 0)
    vk.make_object(v.part("EventFloor"), f"SM_{NAME}_EventFloor", bm, ["M_GB_Floor"])

    # ---- bowl tiers, one mesh per section -----------------------------------
    total = {"lower": 0, "upper": 0}
    end_stage = {"lower": 0, "upper": 0}
    for tier, prefix, mat, base, col in ((lower, 100, "M_GB_SeatLower", 0.0, "BowlLower"),
                                         (upper, 200, "M_GB_SeatUpper", None, "BowlUpper")):
        prof = tier.profile(base_z=base)
        for idx, (t0, t1) in enumerate(section_ranges()):
            sid = f"{'L' if prefix == 100 else 'U'}{prefix + idx + 1}"
            bm = bmesh.new()
            vk.loft_section(bm, path, t0, t1, prof, 0, step=1.5)
            vk.make_object(v.part(col), f"SM_{NAME}_{sid}", bm, [mat])

            seats = []
            vom = prefix == 100 and idx % 2 == 0
            for r in range(tier.rows):
                d = tier.d_front(r) + 0.55
                z = tier.rows_z[r] + 0.45
                row_pts = vk.points_along(path, t0, t1, d, SEAT_W, AISLE)
                mid = len(row_pts) / 2
                for k, (t, p) in enumerate(row_pts):
                    if vom and r < 8 and abs(k + 0.5 - mid) * SEAT_W < 1.3:
                        continue  # vomitory tunnel through the lower rows
                    n = path.normal(t)
                    yaw = math.degrees(math.atan2(-n.y, -n.x))
                    seats.append((p.x, p.y, z, yaw, r + 1, seat_view(p.x)))
            key = "lower" if prefix == 100 else "upper"
            total[key] += len(seats)
            end_stage[key] += sum(1 for s in seats if s[5] < 2)
            centre = path.point((t0 + t1) / 2, tier.d0)
            v.add_section(sid, key, seats, path_range=[round(t0, 4), round(t1, 4)],
                          sold_end_stage=any(s[5] < 2 for s in seats),
                          centre_m=[round(centre.x, 2), round(centre.y, 2)])
            if vom:
                pv = path.point((t0 + t1) / 2, tier.d_front(4))
                v.marker("vomitory", f"Vom_{sid}", (pv.x, pv.y, tier.rows_z[0]),
                         math.degrees(math.atan2(-path.normal((t0 + t1) / 2).y, -path.normal((t0 + t1) / 2).x)),
                         rows=[1, 8], width_m=2.6)

    # ---- suites ring ---------------------------------------------------------
    bm = bmesh.new()
    pts = []
    for seg in range(8):
        pts += vk.points_along(path, seg, seg + 1, (suite_d0 + suite_d1) / 2, SUITE_W, 0.3)
    for t, p in pts:
        n = path.normal(t)
        yaw = math.atan2(n.y, n.x)
        vk.add_box(bm, (p.x, p.y, suite_z + SUITE_H / 2), (SUITE_DEPTH, SUITE_W - 0.2, SUITE_H), yaw, 0)
        g = p - n * (SUITE_DEPTH / 2 + 0.05)
        vk.add_box(bm, (g.x, g.y, suite_z + 1.1), (0.1, SUITE_W - 0.4, 2.2), yaw, 1)
    vk.make_object(v.part("Suites"), f"SM_{NAME}_Suites", bm, ["M_GB_Suite", "M_GB_Glass"])
    v.capacity["suites"] = len(pts)
    v.capacity["suite_seats_est"] = len(pts) * 16

    # ---- concourses, outer wall, roof ---------------------------------------
    bm = bmesh.new()
    vk.ring_band(bm, path, suite_d0 - 0.01, outer_d, suite_z - 0.5, suite_z, 0)      # main concourse
    vk.ring_band(bm, path, upper.d_end + 1.2, outer_d, upper.top_z - 0.5, upper.top_z, 0)  # upper
    vk.ring_band(bm, path, LOWER["d0"], suite_d0, -0.4, 0.0, 0)  # under the lower bowl
    vk.make_object(v.part("Concourse"), f"SM_{NAME}_Concourse", bm, ["M_GB_Concrete"])

    bm = bmesh.new()
    vk.ring_band(bm, path, outer_d, outer_d + 0.6, -0.4, roof_z, 0)
    vk.make_object(v.part("OuterWall"), f"SM_{NAME}_OuterWall", bm, ["M_GB_Wall"])

    bm = bmesh.new()
    vk.add_prism(bm, vk.rounded_rect_poly(path, outer_d + 0.6), roof_z - 0.6, roof_z, 0)
    span_y = FLOOR_W / 2 + outer_d
    for x in range(-36, 37, 6):  # primary roof trusses spanning Y
        vk.add_box(bm, (x, 0, ROOF_STEEL_Z + 0.9), (0.6, 2 * span_y - 6, 1.8), 0, 1)
    vk.make_object(v.part("Roof"), f"SM_{NAME}_Roof", bm, ["M_GB_Roof", "M_GB_Steel"])

    # ---- centre-hung board -------------------------------------------------
    bm = bmesh.new()
    board_z = 22.0
    vk.add_box(bm, (0, 0, board_z + 3.5), (10.0, 8.0, 6.0), 0, 0)
    vk.add_box(bm, (0, 0, board_z + 7.2), (6.0, 5.0, 1.4), 0, 1)
    vk.make_object(v.part("CenterBoard"), f"SM_{NAME}_CenterBoard", bm, ["M_GB_LED", "M_GB_Steel"])
    v.marker("rig_point", "Rig_CenterHung", (0, 0, ROOF_STEEL_Z), load_kg=45000, note="board trims to 22 m for end stage")

    # ---- stage -----------------------------------------------------------------
    deck_cx = (DECK_BACK_X + DECK_FRONT_X) / 2
    deck_d = DECK_FRONT_X - DECK_BACK_X
    bm = bmesh.new()
    vk.add_box(bm, (deck_cx, 0, DECK_H / 2), (deck_d, DECK_W, DECK_H), 0, 0)
    for sgn in (-1, 1):  # wings / production (SL and SR)
        vk.add_box(bm, (deck_cx - 2, sgn * (DECK_W / 2 + 1.6), DECK_H / 2), (deck_d - 4, 3.2, DECK_H), 0, 0)
    vk.make_object(v.part("Stage_Main"), f"SM_{NAME}_Stage_Main", bm, ["M_GB_StageDeck"])

    bm = bmesh.new()
    rw_len = RUNWAY_END_X - DECK_FRONT_X
    vk.add_box(bm, (DECK_FRONT_X + rw_len / 2, 0, DECK_H / 2), (rw_len, RUNWAY_W, DECK_H), 0, 0)
    vk.make_object(v.part("Stage_Runway"), f"SM_{NAME}_Stage_Runway", bm, ["M_GB_StageDeck"])

    bm = bmesh.new()
    vk.add_disc(bm, (BSTAGE_X, 0), BSTAGE_R, 0.0, DECK_H, 40, 0)
    vk.make_object(v.part("Stage_BStage"), f"SM_{NAME}_Stage_BStage", bm, ["M_GB_StageDeck"])

    bm = bmesh.new()  # upstage LED wall + IMAG screens
    led_w, led_h = 20.0, 10.0
    vk.add_box(bm, (DECK_BACK_X + 0.4, 0, DECK_H + 0.5 + led_h / 2), (0.3, led_w, led_h), 0, 0)
    for sgn in (-1, 1):
        vk.add_box(bm, (-17.0, sgn * 15.5, 8.0 + 4.5), (0.3, 6.0, 9.0), math.radians(sgn * -20), 0)
    vk.make_object(v.part("Stage_Video"), f"SM_{NAME}_Stage_Video", bm, ["M_GB_LED"])

    bm = bmesh.new()  # rig trusses over the stage
    for x in (DECK_FRONT_X - 0.5, deck_cx, DECK_BACK_X + 1.5):
        vk.add_box(bm, (x, 0, 16.0), (0.5, DECK_W + 4, 0.5), 0, 0)
    for y in (-DECK_W / 2 - 2, DECK_W / 2 + 2):
        vk.add_box(bm, (deck_cx, y, 16.0), (deck_d + 1, 0.5, 0.5), 0, 0)
    vk.make_object(v.part("Stage_Truss"), f"SM_{NAME}_Stage_Truss", bm, ["M_GB_Steel"])

    bm = bmesh.new()  # barricade, FOH riser
    pit_y = RUNWAY_W / 2 + 1.5

    def fence(p0, p1):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        vk.add_box(bm, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, 0.6), (L, 0.12, 1.2), math.atan2(dy, dx), 0)

    fy = 13.0
    fence((BARRICADE_X, -fy), (BARRICADE_X, -pit_y))
    fence((BARRICADE_X, pit_y), (BARRICADE_X, fy))
    bring = BSTAGE_R + 1.5
    jx = BSTAGE_X - math.sqrt(bring ** 2 - pit_y ** 2)
    for sgn in (-1, 1):
        fence((BARRICADE_X, sgn * pit_y), (jx, sgn * pit_y))
    a0 = math.atan2(pit_y, jx - BSTAGE_X)
    segs = 28
    for k in range(segs):
        a = a0 + (2 * math.pi - 2 * a0) * k / segs
        b = a0 + (2 * math.pi - 2 * a0) * (k + 1) / segs
        fence((BSTAGE_X + bring * math.cos(a), bring * math.sin(a)),
              (BSTAGE_X + bring * math.cos(b), bring * math.sin(b)))
    fx, fw, fd = FOH_X, FOH_SIZE[0], FOH_SIZE[1]
    vk.add_box(bm, (fx, 0, 0.3), (fd, fw, 0.6), 0, 1)
    for p0, p1 in (((fx - fd / 2 - 1, -fw / 2 - 1), (fx - fd / 2 - 1, fw / 2 + 1)),
                   ((fx + fd / 2 + 1, -fw / 2 - 1), (fx + fd / 2 + 1, fw / 2 + 1)),
                   ((fx - fd / 2 - 1, -fw / 2 - 1), (fx + fd / 2 + 1, -fw / 2 - 1)),
                   ((fx - fd / 2 - 1, fw / 2 + 1), (fx + fd / 2 + 1, fw / 2 + 1))):
        fence(p0, p1)
    vk.make_object(v.part("FloorProduction"), f"SM_{NAME}_FloorProduction", bm,
                   ["M_GB_Barricade", "M_GB_StageDeck"])

    # ---- floor GA standing points ------------------------------------------
    sp = 1.0 / math.sqrt(GA_DENSITY)
    floor_poly = vk.rounded_rect_poly(path, LOWER["d0"] - 0.6, 24)

    def inside_poly(x, y, poly):
        c = False
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
        return c

    ga = {"FLOOR_A": [], "FLOOR_B": []}
    x = BARRICADE_X + 0.5
    while x < FLOOR_L / 2:
        y = -FLOOR_W / 2
        while y <= FLOOR_W / 2:
            ok = inside_poly(x, y, floor_poly)
            ok = ok and not (x < jx + 0.5 and abs(y) < pit_y + 0.4)
            ok = ok and math.hypot(x - BSTAGE_X, y) > bring + 0.4
            ok = ok and not (abs(x - fx) < fd / 2 + 1.4 and abs(y) < fw / 2 + 1.4)
            if ok:
                ga["FLOOR_A" if x < 4.0 else "FLOOR_B"].append(
                    (x, y, 0.0, 180.0, 0, 0))
            y += sp
        x += sp
    for sid, pts_ in ga.items():
        v.add_section(sid, "floor_ga", pts_, standing=True, density_per_m2=GA_DENSITY,
                      sold_end_stage=True)

    # ---- capacity -------------------------------------------------------
    ga_total = sum(len(p) for p in ga.values())
    v.capacity.update({
        "bowl_seats_total": total["lower"] + total["upper"],
        "lower_bowl_seats": total["lower"],
        "upper_bowl_seats": total["upper"],
        "end_stage_bowl_seats_sold": end_stage["lower"] + end_stage["upper"],
        "floor_ga_standing": ga_total,
        "end_stage_concert_total": end_stage["lower"] + end_stage["upper"] + ga_total,
        "end_stage_total_incl_suites": end_stage["lower"] + end_stage["upper"] + ga_total + len(pts) * 16,
        "ga_density_per_m2": GA_DENSITY,
    })

    # ---- stage zones & performer marks ----------------------------------
    v.zone("stage_zone", "Zone_MainDeck", (deck_cx, 0, DECK_H), (deck_d, DECK_W, 0))
    v.zone("stage_zone", "Zone_Runway", (DECK_FRONT_X + rw_len / 2, 0, DECK_H), (rw_len, RUNWAY_W, 0))
    v.zone("stage_zone", "Zone_BStage", (BSTAGE_X, 0, DECK_H), (2 * BSTAGE_R, 2 * BSTAGE_R, 0), shape="disc")
    v.zone("stage_zone", "Zone_Wing_SL", (deck_cx - 2, DECK_W / 2 + 1.6, DECK_H), (deck_d - 4, 3.2, 0))
    v.zone("stage_zone", "Zone_Wing_SR", (deck_cx - 2, -DECK_W / 2 - 1.6, DECK_H), (deck_d - 4, 3.2, 0))
    v.zone("stage_zone", "Zone_LEDWall", (DECK_BACK_X + 0.4, 0, DECK_H + 0.5 + led_h / 2), (0.3, led_w, led_h))
    v.zone("crowd_zone", "Zone_Pit", ((BARRICADE_X + DECK_FRONT_X) / 2, 0, 0), (1.5, 2 * fy, 2.0), note="security only")
    v.zone("crowd_zone", "Zone_FOH", (fx, 0, 0.6), (fd, fw, 3.0))
    v.zone("crowd_zone", "Zone_FloorA", ((BARRICADE_X + 4) / 2, 0, 0), (4 - BARRICADE_X, FLOOR_W, 2.0),
           section="FLOOR_A")
    v.zone("crowd_zone", "Zone_FloorB", ((4 + FLOOR_L / 2) / 2, 0, 0), (FLOOR_L / 2 - 4, FLOOR_W, 2.0),
           section="FLOOR_B")
    for mid, x in (("Mark_Upstage", DECK_BACK_X + 4), ("Mark_Center", deck_cx + 2),
                   ("Mark_Downstage", DECK_FRONT_X - 1.5), ("Mark_RunwayMid", (DECK_FRONT_X + RUNWAY_END_X) / 2),
                   ("Mark_BStage", BSTAGE_X)):
        v.marker("performer_mark", mid, (x, 0, DECK_H), 0.0)
    for sgn, side in ((1, "SL"), (-1, "SR")):
        v.marker("performer_mark", f"Mark_Dancer_{side}1", (deck_cx + 1, sgn * 5, DECK_H), 0.0)
        v.marker("performer_mark", f"Mark_Dancer_{side}2", (deck_cx - 2, sgn * 8, DECK_H), 0.0)
        v.marker("performer_mark", f"Mark_Entrance_{side}", (deck_cx - 2, sgn * (DECK_W / 2 + 1.6), DECK_H),
                 -90.0 * sgn)

    # ---- rigging -------------------------------------------------------
    for x in range(-30, 31, 3):
        for y in range(-15, 16, 3):
            v.marker("rig_grid", f"Grid_{x:+03d}_{y:+03d}", (x, y, ROOF_STEEL_Z), load_kg=1000)
    for i, y in enumerate((-9, -3, 3, 9)):
        v.marker("rig_point", f"Rig_LEDWall_{i + 1}", (DECK_BACK_X + 0.4, y, ROOF_STEEL_Z), load_kg=2000)
    for name_, x in (("Front", DECK_FRONT_X - 0.5), ("Mid", deck_cx), ("Back", DECK_BACK_X + 1.5)):
        for y in (-DECK_W / 2 - 2, 0, DECK_W / 2 + 2):
            v.marker("rig_point", f"Rig_Truss{name_}_{'SR' if y < 0 else 'SL' if y > 0 else 'C'}",
                     (x, y, ROOF_STEEL_Z), load_kg=1500, trim_m=16.0)
    for sgn, side in ((1, "SL"), (-1, "SR")):
        v.marker("rig_point", f"Rig_PA_Main_{side}", (DECK_FRONT_X - 1, sgn * 13.5, ROOF_STEEL_Z), load_kg=3000, trim_m=14.0)
        v.marker("rig_point", f"Rig_PA_Side_{side}", (DECK_FRONT_X + 4, sgn * 16.5, ROOF_STEEL_Z), load_kg=2500, trim_m=15.0)
        v.marker("rig_point", f"Rig_IMAG_{side}", (-17.0, sgn * 15.5, ROOF_STEEL_Z), load_kg=1500, trim_m=8.0)
        v.marker("rig_point", f"Rig_DelayPA_{side}", (8.0, sgn * 14.0, ROOF_STEEL_Z), load_kg=1200, trim_m=16.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            v.marker("rig_point", f"Rig_Spidercam_{'E' if sx > 0 else 'W'}{'N' if sy > 0 else 'S'}",
                     (sx * 40.0, sy * 32.0, ROOF_STEEL_Z - 3), load_kg=800)
    for sgn in (1, -1):  # FX positions along the downstage edge
        for i, y in enumerate((4.0, 9.0)):
            v.marker("fx_point", f"FX_Pyro_DS_{'SL' if sgn > 0 else 'SR'}{i + 1}", (DECK_FRONT_X - 0.3, sgn * y, DECK_H), 0.0)
        v.marker("fx_point", f"FX_CO2_{'SL' if sgn > 0 else 'SR'}", (DECK_FRONT_X - 0.5, sgn * 10.8, DECK_H), 0.0)
        v.marker("fx_point", f"FX_Confetti_{'SL' if sgn > 0 else 'SR'}", (6.0, sgn * 14.0, 0.0), 0.0)
        v.marker("fx_point", f"FX_Laser_{'SL' if sgn > 0 else 'SR'}", (DECK_BACK_X + 2, sgn * 10.5, DECK_H + 0.2), 0.0)
    v.marker("fx_point", "FX_Haze_US", (DECK_BACK_X + 1, 0, DECK_H), 0.0)

    # ---- cameras -----------------------------------------------------------
    stage_t = (deck_cx + 3, 0, DECK_H + 1.7)
    v.look_at("camera", "Cam_FOH_Wide", (FOH_X, 0, 4.5), stage_t, lens_mm=35)
    v.look_at("camera", "Cam_FOH_Tele", (FOH_X - 1, 0.8, 4.5), (deck_cx + 4, 0, DECK_H + 1.6), lens_mm=200)
    v.look_at("camera", "Cam_Pit_Dolly_Start", (BARRICADE_X - 0.7, -10, 1.4), (deck_cx, 0, DECK_H + 1.6),
              lens_mm=24, track_end_m=[BARRICADE_X - 0.7, 10, 1.4])
    v.look_at("camera", "Cam_Runway_End", (RUNWAY_END_X + 1.5, 2.5, 1.0), (DECK_FRONT_X, 0, DECK_H + 1.7), lens_mm=50)
    for sgn, side in ((1, "SL"), (-1, "SR")):
        v.look_at("camera", f"Cam_Wing_{side}", (deck_cx + 1, sgn * (DECK_W / 2 + 1), DECK_H + 1.6),
                  (DECK_FRONT_X, -sgn * 2, DECK_H + 1.6), lens_mm=24, handheld=True)
        p = path.point(2.5 if sgn > 0 else 6.5, lower.d_front(14))
        v.look_at("camera", f"Cam_LowerBowl_{side}", (p.x, p.y, lower.rows_z[14] + 1.5), stage_t, lens_mm=85)
    pe = path.point(0.5, upper.d_front(UPPER_ROWS - 2))
    v.look_at("camera", "Cam_UpperBowl_EastWide", (pe.x, pe.y, upper.rows_z[-2] + 1.6), (deck_cx, 0, 4.0), lens_mm=28)
    v.look_at("camera", "Cam_Spidercam", (-4.0, 0, 14.0), stage_t, lens_mm=24, rig="Rig_Spidercam_*")
    v.look_at("camera", "Cam_CrowdPOV", (6.0, 4.0, 1.65), stage_t, lens_mm=18, note="fan eye height")
    v.look_at("camera", "Cam_Overhead", (-20.0, 0, 28.0), (-20.5, 0, 0), lens_mm=18)

    meta = dict(lower=lower, upper=upper, outer_d=outer_d, roof_z=roof_z, path=path)
    return v, meta


VIEWS = {
    "aerial": ((95, -85, 70), (-5, 0, 5), 30, None),
    "foh": ((FOH_X - 4, 0, 4.5), (-21, 0, 6), 22, None),
    "upper_bowl": ((38, 45, 24), (-15, 0, 4), 24, None),
    "plan": ((0, 0, 200), (0, 0, 0), None, 150),
}
