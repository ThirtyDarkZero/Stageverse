"""venuekit: small toolkit for script-generated venue blockouts in Blender.

Everything is built in real-world meters, Z up, with the stage at -X and the
venue symmetric about the X axis (so Blender->Unreal's Y mirror never matters).

A venue is a set of *parts* (one Blender collection each, exported as one FBX
per part) plus *markers* (rig points, cameras, stage zones, crowd zones,
performer marks) and *seats* (instance points for the crowd system), written
to JSON next to the FBX files.

Run inside Blender's Python (bpy). See build_venues.py.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field

import bpy  # must come before bmesh/mathutils when using the bpy wheel
import bmesh
from mathutils import Vector

# --------------------------------------------------------------------------
# Greybox material palette. Names are the material slots Rob swaps for Fab
# material instances in Unreal; keep them stable.
# --------------------------------------------------------------------------
PALETTE = {
    "M_GB_Concrete": (0.55, 0.55, 0.55),
    "M_GB_Floor": (0.32, 0.30, 0.28),
    "M_GB_SeatLower": (0.45, 0.12, 0.14),
    "M_GB_SeatUpper": (0.16, 0.22, 0.42),
    "M_GB_SeatBalcony": (0.42, 0.18, 0.40),
    "M_GB_Suite": (0.70, 0.62, 0.45),
    "M_GB_Glass": (0.35, 0.55, 0.65),
    "M_GB_StageDeck": (0.08, 0.08, 0.08),
    "M_GB_LED": (0.10, 0.35, 0.45),
    "M_GB_Steel": (0.75, 0.68, 0.20),
    "M_GB_Wall": (0.62, 0.60, 0.56),
    "M_GB_Roof": (0.40, 0.42, 0.45),
    "M_GB_Barricade": (0.80, 0.80, 0.80),
    "M_GB_Bar": (0.36, 0.22, 0.12),
    "M_GB_Curtain": (0.35, 0.03, 0.05),
}


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.unit_settings.system = "METRIC"
    s.unit_settings.scale_length = 1.0
    for name, rgb in PALETTE.items():
        m = bpy.data.materials.new(name)
        m.diffuse_color = (*rgb, 1.0)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.8
        if name == "M_GB_LED":
            bsdf.inputs["Emission Color"].default_value = (*rgb, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 2.0


# --------------------------------------------------------------------------
# Paths: a centre line with an outward normal. point(t, d) offsets the line by
# d meters along its outward normal (seating rows rise as d grows).
# --------------------------------------------------------------------------
class RoundedRect:
    """Rounded rectangle of overall L (X) x W (Y), corner radius R, centred on
    (cx, 0). Parameter s runs 0..8 counter-clockwise in eight segments:
    0 east straight, 1 NE arc, 2 north straight, 3 NW arc, 4 west straight,
    5 SW arc, 6 south straight, 7 SE arc. The stage end is segment 4 (west)."""

    def __init__(self, L, W, R, cx=0.0):
        self.hx = L / 2 - R
        self.hy = W / 2 - R
        self.R = R
        self.cx = cx

    def _seg(self, s):
        i = min(int(s), 7)
        return i, s - i

    def normal(self, s):
        i, u = self._seg(s)
        if i % 2 == 0:
            return [Vector((1, 0)), Vector((0, 1)), Vector((-1, 0)), Vector((0, -1))][i // 2]
        a0 = [0, 90, 180, 270][i // 2]
        a = math.radians(a0 + 90 * u)
        return Vector((math.cos(a), math.sin(a)))

    def point(self, s, d):
        i, u = self._seg(s)
        hx, hy, r = self.hx, self.hy, self.R + d
        if i == 0:
            p = Vector((hx + r, -hy + 2 * hy * u))
        elif i == 2:
            p = Vector((hx - 2 * hx * u, hy + r))
        elif i == 4:
            p = Vector((-hx - r, hy - 2 * hy * u))
        elif i == 6:
            p = Vector((-hx + 2 * hx * u, -hy - r))
        else:
            c = {1: (hx, hy), 3: (-hx, hy), 5: (-hx, -hy), 7: (hx, -hy)}[i]
            p = Vector(c) + r * self.normal(s)
        return p + Vector((self.cx, 0))


class LinePath:
    """Straight centre line p0->p1 (2D) with an explicit outward normal n."""

    def __init__(self, p0, p1, n):
        self.p0, self.p1 = Vector(p0), Vector(p1)
        self.n = Vector(n).normalized()

    def normal(self, t):
        return self.n

    def point(self, t, d):
        return self.p0.lerp(self.p1, t) + d * self.n


def path_length(path, t0, t1, d, n=200):
    pts = [path.point(t0 + (t1 - t0) * k / n, d) for k in range(n + 1)]
    return sum((pts[k + 1] - pts[k]).length for k in range(n))


def points_along(path, t0, t1, d, spacing, margin):
    """Evenly spaced points (t, xy) along the path at offset d, with `margin`
    meters kept clear at both ends (aisles). Centred in the available run."""
    n = 400
    ts = [t0 + (t1 - t0) * k / n for k in range(n + 1)]
    pts = [path.point(t, d) for t in ts]
    cum = [0.0]
    for k in range(n):
        cum.append(cum[-1] + (pts[k + 1] - pts[k]).length)
    total = cum[-1]
    usable = total - 2 * margin
    if usable < spacing:
        return []
    count = int(usable // spacing)
    start = margin + (usable - count * spacing) / 2 + spacing / 2
    out, j = [], 0
    for c in range(count):
        target = start + c * spacing
        while j < n - 1 and cum[j + 1] < target:
            j += 1
        f = (target - cum[j]) / max(cum[j + 1] - cum[j], 1e-9)
        t = ts[j] + f * (ts[j + 1] - ts[j])
        out.append((t, path.point(t, d)))
    return out


# --------------------------------------------------------------------------
# Rows: a seating tier is a list of rows (d_front, z_tread) plus a depth.
# --------------------------------------------------------------------------
@dataclass
class Tier:
    name: str
    d0: float               # offset of the first row's front edge
    z0: float               # tread height of the first row
    rows: int
    row_depth: float
    rise_first: float       # riser height of the first step
    rise_last: float        # riser height of the last step (C-value curve)
    front_wall: float = 1.0 # height of the front fascia / rail wall above z0
    underside_drop: float = 1.5  # thickness of the tier slab below the front
    rows_z: list = field(default_factory=list)

    def __post_init__(self):
        z = self.z0
        self.rows_z = []
        for i in range(self.rows):
            self.rows_z.append(z)
            f = i / max(self.rows - 1, 1)
            z += self.rise_first + (self.rise_last - self.rise_first) * f
        self.top_z = z  # height of the step behind the last row (cross aisle)

    def d_front(self, i):
        return self.d0 + i * self.row_depth

    @property
    def d_end(self):
        return self.d0 + self.rows * self.row_depth

    def profile(self, base_z=None):
        """Closed (d, z) loop: front rail wall, staircase, cross aisle, then
        either a raked underside (base_z None) or straight down to base_z."""
        bz = self.z0 - self.underside_drop if base_z is None else base_z
        pts = [(self.d0, bz), (self.d0, self.z0 + self.front_wall),
               (self.d0 + 0.25, self.z0 + self.front_wall), (self.d0 + 0.25, self.z0)]
        for i, z in enumerate(self.rows_z):
            pts.append((self.d_front(i) + self.row_depth, z))
            nz = self.rows_z[i + 1] if i + 1 < self.rows else self.top_z
            pts.append((self.d_front(i) + self.row_depth, nz))
        back = self.d_end + 1.2                      # cross aisle behind last row
        pts.append((back, self.top_z))
        pts.append((back, self.top_z - 0.6 if base_z is None else base_z))
        return pts


# --------------------------------------------------------------------------
# Mesh building
# --------------------------------------------------------------------------
def _box_uv(bm, scale=1.0):
    """World-aligned box projection so tiling materials work out of the box."""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda k: abs(n[k]))
        for l in f.loops:
            co = l.vert.co
            if ax == 0:
                l[uv].uv = (co.y / scale, co.z / scale)
            elif ax == 1:
                l[uv].uv = (co.x / scale, co.z / scale)
            else:
                l[uv].uv = (co.x / scale, co.y / scale)


def make_object(collection, name, bm, materials):
    """materials: list of material names; faces must carry material_index."""
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _box_uv(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in materials:
        me.materials.append(bpy.data.materials[m])
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    return ob


def loft_section(bm, path, t0, t1, profile, mat_index=0, step=1.5):
    """Sweep a closed (d, z) profile along path from t0 to t1, capped."""
    dmax = max(p[0] for p in profile)
    length = path_length(path, t0, t1, dmax, 60)
    n = max(2, int(math.ceil(length / step)))
    rings = []
    for k in range(n + 1):
        t = t0 + (t1 - t0) * k / n
        ring = []
        for d, z in profile:
            xy = path.point(t, d)
            ring.append(bm.verts.new((xy.x, xy.y, z)))
        rings.append(ring)
    m = len(profile)
    for k in range(n):
        a, b = rings[k], rings[k + 1]
        for j in range(m):
            j2 = (j + 1) % m
            f = bm.faces.new((a[j], a[j2], b[j2], b[j]))
            f.material_index = mat_index
    for ring in (rings[0], rings[-1]):
        f = bm.faces.new(ring)
        f.material_index = mat_index
    bm.normal_update()  # triangulate needs valid face normals for concave n-gons
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])


def add_box(bm, center, size, yaw=0.0, mat_index=0):
    cx, cy, cz = center
    sx, sy, sz = (s / 2 for s in size)
    c, s = math.cos(yaw), math.sin(yaw)
    vs = []
    for dz in (-sz, sz):
        for dx, dy in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)):
            vs.append(bm.verts.new((cx + dx * c - dy * s, cy + dx * s + dy * c, cz + dz)))
    idx = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for q in idx:
        f = bm.faces.new([vs[i] for i in q])
        f.material_index = mat_index


def add_prism(bm, poly2d, z0, z1, mat_index=0):
    """Vertical extrusion of a convex-or-not 2D polygon."""
    bot = [bm.verts.new((x, y, z0)) for x, y in poly2d]
    top = [bm.verts.new((x, y, z1)) for x, y in poly2d]
    n = len(poly2d)
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((bot[i], bot[j], top[j], top[i]))
        f.material_index = mat_index
    for ring in (list(reversed(bot)), top):
        f = bm.faces.new(ring)
        f.material_index = mat_index
    bm.normal_update()  # triangulate needs valid face normals for concave n-gons
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])


def add_disc(bm, center, radius, z0, z1, segs=32, mat_index=0):
    cx, cy = center
    poly = [(cx + radius * math.cos(2 * math.pi * k / segs), cy + radius * math.sin(2 * math.pi * k / segs))
            for k in range(segs)]
    add_prism(bm, poly, z0, z1, mat_index)


def ring_band(bm, path, d0, d1, z0, z1, mat_index=0, step=2.0, segments=None):
    """Closed band between offsets d0..d1 and heights z0..z1 all the way round
    a RoundedRect (walls, concourse slabs, roof rings)."""
    segments = segments or [(i, i + 1) for i in range(8)]
    prof = [(d0, z0), (d1, z0), (d1, z1), (d0, z1)]
    for t0, t1 in segments:
        loft_section(bm, path, t0, t1, prof, mat_index, step)


def rounded_rect_poly(path, d, per_seg=12):
    pts = []
    for i in range(8):
        k = per_seg if i % 2 else 1
        for j in range(k):
            pts.append(tuple(path.point(i + j / k, d)))
    return pts


# --------------------------------------------------------------------------
# Venue: parts + markers + seats + export
# --------------------------------------------------------------------------
def to_ue_cm(x, y, z):
    """Blender meters (right-handed, Z up) -> Unreal cm (left-handed): Y flips."""
    return [round(x * 100, 1), round(-y * 100, 1), round(z * 100, 1)]


class Venue:
    def __init__(self, name, title, notes=""):
        reset_scene()
        self.name = name
        self.title = title
        self.notes = notes
        self.parts = {}
        self.markers = []
        self.sections = []
        self.capacity = {}

    def part(self, part_name):
        if part_name not in self.parts:
            col = bpy.data.collections.new(f"SM_{self.name}_{part_name}")
            bpy.context.scene.collection.children.link(col)
            self.parts[part_name] = col
        return self.parts[part_name]

    # ---- markers -----------------------------------------------------------
    def marker(self, mtype, mid, loc, yaw_deg=0.0, pitch_deg=0.0, **props):
        x, y, z = loc
        m = {
            "id": mid, "type": mtype,
            "loc_m": [round(x, 3), round(y, 3), round(z, 3)],
            "ue_loc_cm": to_ue_cm(x, y, z),
            "ue_rot_deg": {"yaw": round(-yaw_deg, 2), "pitch": round(pitch_deg, 2), "roll": 0.0},
        }
        m.update(props)
        self.markers.append(m)
        return m

    def look_at(self, mtype, mid, loc, target, **props):
        dx, dy, dz = (target[i] - loc[i] for i in range(3))
        yaw = math.degrees(math.atan2(dy, dx))
        pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
        return self.marker(mtype, mid, loc, yaw, pitch, target_m=list(target), **props)

    def zone(self, mtype, mid, center, size, **props):
        return self.marker(mtype, mid, center, size_m=[round(v, 3) for v in size],
                           ue_size_cm=[round(v * 100, 1) for v in size], **props)

    # ---- seats -------------------------------------------------------------
    def add_section(self, sid, tier, seats, **props):
        """seats: list of (x, y, z, yaw_deg, row, view) in Blender meters.
        view: 0 clear, 1 limited/side view, 2 not sold in the end-stage config."""
        self.sections.append({"id": sid, "tier": tier, "seats": seats, **props})

    # ---- export ------------------------------------------------------------
    def export(self, outdir):
        os.makedirs(outdir, exist_ok=True)
        files = []
        for part_name, col in self.parts.items():
            bpy.ops.object.select_all(action="DESELECT")
            obs = [o for o in col.all_objects if o.type == "MESH"]
            if not obs:
                continue
            for o in obs:
                o.select_set(True)
            bpy.context.view_layer.objects.active = obs[0]
            fn = f"SM_{self.name}_{part_name}.fbx"
            bpy.ops.export_scene.fbx(
                filepath=os.path.join(outdir, fn), use_selection=True,
                object_types={"MESH"}, apply_unit_scale=True,
                apply_scale_options="FBX_SCALE_NONE", mesh_smooth_type="FACE",
                use_mesh_modifiers=True, add_leaf_bones=False, bake_anim=False,
                path_mode="STRIP")
            tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in obs)
            files.append({"file": fn, "part": part_name, "objects": [o.name for o in obs], "tris": tris})

        markers = {
            "venue": self.name, "title": self.title, "notes": self.notes,
            "units": "loc_m: Blender meters, Z up, stage at -X. ue_loc_cm: Unreal cm (Y flipped). "
                     "The venue is symmetric about X so the flip never moves geometry.",
            "capacity": self.capacity, "parts": files, "markers": self.markers,
        }
        with open(os.path.join(outdir, "markers.json"), "w") as f:
            json.dump(markers, f, indent=1)

        seats_out = {
            "venue": self.name,
            "format": "Each seat is [x_cm, y_cm, z_cm, yaw_deg, row, view] in Unreal space (cm, Y flipped "
                      "from Blender). z is the standing/seat-pan reference height; yaw faces the stage or "
                      "event floor. view: 0 clear, 1 limited/side view, 2 not sold in the end-stage config "
                      "(behind the stage). Floor GA 'seats' are standing spots at the configured density.",
            "sections": [],
        }
        for s in self.sections:
            seats = [[*to_ue_cm(x, y, z), round(-yaw, 1), row, view] for (x, y, z, yaw, row, view) in s["seats"]]
            entry = {k: v for k, v in s.items() if k != "seats"}
            entry["count"] = len(seats)
            entry["seats"] = seats
            seats_out["sections"].append(entry)
        with open(os.path.join(outdir, "seats.json"), "w") as f:
            json.dump(seats_out, f, separators=(",", ":"))
        return files


# --------------------------------------------------------------------------
# Preview rendering (Cycles CPU; EEVEE/Workbench need a GPU context)
# --------------------------------------------------------------------------
def render_views(venue, outdir, views, hide_parts=(), res=(1600, 900), samples=24):
    os.makedirs(outdir, exist_ok=True)
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = samples
    try:
        scn.cycles.use_denoising = True
    except Exception:
        pass
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.film_transparent = False
    scn.view_settings.view_transform = "Standard"
    if scn.world is None:
        scn.world = bpy.data.worlds.new("World")
    scn.world.use_nodes = True
    bg = scn.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.82, 0.85, 0.9, 1)
    bg.inputs["Strength"].default_value = 0.9
    if not any(o.type == "LIGHT" for o in scn.objects):
        sun = bpy.data.lights.new("Sun", "SUN")
        sun.energy = 3.0
        sun.angle = math.radians(8)
        so = bpy.data.objects.new("Sun", sun)
        so.rotation_euler = (math.radians(40), math.radians(15), math.radians(35))
        scn.collection.objects.link(so)
    out = []
    for vname, spec in views.items():
        loc, target, lens, ortho = spec[:4]
        hide = spec[4] if len(spec) > 4 else hide_parts
        for p, col in venue.parts.items():
            col.hide_render = p in hide
        cam_data = bpy.data.cameras.new(vname)
        if ortho:
            cam_data.type = "ORTHO"
            cam_data.ortho_scale = ortho
        else:
            cam_data.lens = lens
        cam_data.clip_end = 2000
        cam = bpy.data.objects.new(vname, cam_data)
        scn.collection.objects.link(cam)
        cam.location = loc
        direction = Vector(target) - Vector(loc)
        cam.rotation_euler = direction.to_track_quat("-Z", "Y" if not ortho else "Y").to_euler()
        scn.camera = cam
        path = os.path.join(outdir, f"{venue.name}_{vname}.png")
        scn.render.filepath = path
        bpy.ops.render.render(write_still=True)
        out.append(path)
    for col in venue.parts.values():
        col.hide_render = False
    return out
