"""Retarget tracked dancer poses (track_dancer.py JSON) onto a Meshy-rigged character and export an FBX animation.

Each frame, every limb bone is swung to point along the matching body segment of the tracked dancer
(shoulder->elbow, elbow->wrist, hip->knee...), the hips and chest take their full orientation from the
hip and shoulder lines, and the hips are lifted/lowered so the lower foot stays on the floor.
Poses are lightly smoothed over time and the end blends back into the start so the clip loops.

    python pipeline/motion/retarget_meshy.py --rig SK_ArizonaRae.fbx --poses poses.json --out A_Dance.fbx [--preview sheet.png]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy  # type: ignore
import numpy as np
from mathutils import Matrix, Vector  # type: ignore

# MediaPipe Pose landmark ids
NOSE, L_EAR, R_EAR = 0, 7, 8
L_SH, R_SH, L_EL, R_EL, L_WR, R_WR = 11, 12, 13, 14, 15, 16
L_PI, R_PI, L_IN, R_IN = 17, 18, 19, 20
L_HIP, R_HIP, L_KN, R_KN, L_AN, R_AN = 23, 24, 25, 26, 27, 28
L_FI, R_FI = 31, 32

# bone -> (from landmark(s), to landmark(s)); a tuple means the mean of those landmarks
SWING = [
    ("LeftArm", L_SH, L_EL), ("LeftForeArm", L_EL, L_WR), ("LeftHand", L_WR, (L_PI, L_IN)),
    ("RightArm", R_SH, R_EL), ("RightForeArm", R_EL, R_WR), ("RightHand", R_WR, (R_PI, R_IN)),
    ("LeftUpLeg", L_HIP, L_KN), ("LeftLeg", L_KN, L_AN), ("LeftFoot", L_AN, L_FI),
    ("RightUpLeg", R_HIP, R_KN), ("RightLeg", R_KN, R_AN), ("RightFoot", R_AN, R_FI),
]


def load_poses(path: Path, smooth: float, loop_frames: int) -> tuple[np.ndarray, float]:
    doc = json.loads(path.read_text())
    frames = doc["frames"]
    P = np.full((len(frames), 33, 3), np.nan)
    for i, f in enumerate(frames):
        if f.get("ok"):
            w = np.array(f["world"])
            P[i] = np.stack([w[:, 0], w[:, 2], -w[:, 1]], axis=1)  # MediaPipe (x right, y down, z to camera) -> Blender (Z up, camera at -Y)
    for j in range(33):  # fill gaps by interpolation
        for k in range(3):
            v = P[:, j, k]
            bad = np.isnan(v)
            if bad.all():
                v[:] = 0
            elif bad.any():
                v[bad] = np.interp(np.flatnonzero(bad), np.flatnonzero(~bad), v[~bad])
    if smooth > 0:
        r = int(math.ceil(smooth * 3))
        k = np.exp(-0.5 * (np.arange(-r, r + 1) / smooth) ** 2)
        k /= k.sum()
        pad = np.concatenate([P[:1].repeat(r, 0), P, P[-1:].repeat(r, 0)])
        P = np.stack([np.tensordot(k, pad[i:i + 2 * r + 1], axes=(0, 0)) for i in range(len(P))])
    n = min(loop_frames, len(P) // 4)
    for i in range(n):  # blend the tail into the first frame so the clip loops
        a = (i + 1) / n
        P[len(P) - n + i] = (1 - a) * P[len(P) - n + i] + a * P[0]
    return P, doc["fps"]


def pt(P, f, j):
    if isinstance(j, tuple):
        return Vector(np.mean([P[f, k] for k in j], axis=0))
    return Vector(P[f, j])


def frame(across: Vector, up: Vector) -> Matrix:
    x = across.normalized()
    z = (up - x * up.dot(x)).normalized()
    y = z.cross(x)
    return Matrix((x, y, z)).transposed()


def set_rot(pb, rot3: Matrix, loc: Vector | None = None):
    m = pb.matrix.copy()
    new = rot3.to_4x4()
    new.translation = loc if loc is not None else m.translation
    pb.matrix = new
    bpy.context.view_layer.update()


def swing(pb, d: Vector):
    cur = pb.matrix.to_3x3()
    y = Vector(cur.col[1])
    if d.length < 1e-6:
        return
    q = y.rotation_difference(d.normalized())
    set_rot(pb, q.to_matrix() @ cur)


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--rig", required=True, type=Path)
    ap.add_argument("--poses", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--name", default="Dance")
    ap.add_argument("--smooth", type=float, default=1.2, help="gaussian sigma in frames")
    ap.add_argument("--loop-frames", type=int, default=12)
    ap.add_argument("--preview", type=Path)
    ap.add_argument("--preview-all", action="store_true", help="render every frame (for a preview video)")
    a = ap.parse_args(argv)

    P, fps = load_poses(a.poses, a.smooth, a.loop_frames)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(a.rig))
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    bones = arm.data.bones
    scn = bpy.context.scene
    scn.render.fps, scn.render.fps_base = round(fps), round(fps) / fps
    scn.frame_start, scn.frame_end = 1, len(P)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    pbs = arm.pose.bones

    rest = {b.name: b.matrix_local.copy() for b in bones}
    hips_rest = rest["Hips"].to_3x3()
    chest_rest = rest["Spine"].to_3x3()
    head_rest = rest["Head"].to_3x3()
    rest_across_hip = (bones["LeftUpLeg"].head_local - bones["RightUpLeg"].head_local)
    rest_across_sh = (bones["LeftArm"].head_local - bones["RightArm"].head_local)
    rest_up = Vector((0, 0, 1))
    leg_rest = (bones["LeftUpLeg"].head_local - bones["LeftLeg"].head_local).length + \
               (bones["LeftLeg"].head_local - bones["LeftFoot"].head_local).length
    ankle_z = bones["LeftFoot"].head_local.z
    hip_above_legs = bones["Hips"].head_local.z - bones["LeftUpLeg"].head_local.z
    hips_xy = bones["Hips"].head_local.xy

    act = bpy.data.actions.new(a.name)
    arm.animation_data_create().action = act
    for f in range(len(P)):
        scn.frame_set(f + 1)
        for pb in pbs:
            pb.matrix_basis = Matrix.Identity(4)
        bpy.context.view_layer.update()
        hip_mid = (pt(P, f, L_HIP) + pt(P, f, R_HIP)) / 2
        sh_mid = (pt(P, f, L_SH) + pt(P, f, R_SH)) / 2
        ear_mid = (pt(P, f, L_EAR) + pt(P, f, R_EAR)) / 2
        up = sh_mid - hip_mid
        # hips: orientation from the hip line, height so the lower ankle sits at rest ankle height
        leg_mp = ((pt(P, f, L_HIP) - pt(P, f, L_KN)).length + (pt(P, f, L_KN) - pt(P, f, L_AN)).length +
                  (pt(P, f, R_HIP) - pt(P, f, R_KN)).length + (pt(P, f, R_KN) - pt(P, f, R_AN)).length) / 2
        s = leg_rest / max(leg_mp, 1e-3)
        low = min(pt(P, f, L_AN).z, pt(P, f, R_AN).z)
        hz = s * (hip_mid.z - low) + ankle_z + hip_above_legs
        rot = frame(pt(P, f, L_HIP) - pt(P, f, R_HIP), up) @ frame(rest_across_hip, rest_up).transposed() @ hips_rest
        set_rot(pbs["Hips"], rot, Vector((hips_xy.x, hips_xy.y, hz)))
        # spine bends toward the shoulders, chest takes the shoulder line
        for name in ("Spine02", "Spine01"):
            swing(pbs[name], up)
        rot = frame(pt(P, f, L_SH) - pt(P, f, R_SH), up) @ frame(rest_across_sh, rest_up).transposed() @ chest_rest
        set_rot(pbs["Spine"], rot)
        head_up = (ear_mid - sh_mid).normalized() + up.normalized()  # halve the head's forward drop (ear depth is noisy)
        swing(pbs["neck"], head_up)
        rot = frame(pt(P, f, L_EAR) - pt(P, f, R_EAR), head_up) @ frame(Vector((1, 0, 0)), rest_up).transposed() @ head_rest
        set_rot(pbs["Head"], rot)
        for name, i, j in SWING:
            swing(pbs[name], pt(P, f, j) - pt(P, f, i))
        for pb in pbs:
            pb.keyframe_insert("location", frame=f + 1, group=pb.name)
            pb.rotation_mode = "QUATERNION"
            pb.keyframe_insert("rotation_quaternion", frame=f + 1, group=pb.name)
    bpy.ops.object.mode_set(mode="OBJECT")
    print(f"ANIM {a.name}: {len(P)} frames at {fps:.3f} fps")

    a.out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=str(a.out), use_selection=False, object_types={"ARMATURE", "MESH"},
                             add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False,
                             bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                             bake_anim_simplify_factor=0.0, path_mode="STRIP", embed_textures=False,
                             primary_bone_axis="Y", secondary_bone_axis="X")
    print(f"FBX -> {a.out}")

    if a.preview:
        scn.render.engine = "CYCLES"
        scn.cycles.device = "CPU"
        scn.cycles.samples = 8
        scn.render.resolution_x, scn.render.resolution_y = 300, 420
        world = bpy.data.worlds.new("w")
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs[1].default_value = 2.0
        scn.world = world
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
        scn.collection.objects.link(cam)
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = 2.1
        cam.location = (0, -6, 0.95)
        sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
        sun.data.energy = 4
        sun.rotation_euler = (math.radians(70), 0, math.radians(-15))
        scn.collection.objects.link(sun)
        cam.rotation_euler = (math.radians(90), 0, 0)
        scn.camera = cam
        outs = []
        picks = range(1, len(P) + 1) if a.preview_all else np.linspace(1, len(P), 12).astype(int)
        for k, f in enumerate(picks):
            scn.frame_set(int(f))
            p = a.preview.with_name(f"{a.preview.stem}_{k:03d}.png")
            scn.render.filepath = str(p)
            bpy.ops.render.render(write_still=True)
            outs.append(str(p))
        print("PREVIEWS " + " ".join(outs))


if __name__ == "__main__":
    main()
