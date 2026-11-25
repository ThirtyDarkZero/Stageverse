"""Track one dancer's body pose through a clip and save 3D landmarks per frame.

Finds every person with YOLOv8, picks the dancer by a colour cue on the torso (default: the red
corset) plus continuity with the last frame, crops tightly around her and runs MediaPipe Pose (heavy)
on that crop, so other dancers in a class video are ignored. Output JSON: fps + frames of 33 world landmarks (metres, hip-centred)
plus visibility, and an overlay MP4 for checking.

    python pipeline/motion/track_dancer.py --video in.mp4 --start 17 --end 28.5 --out poses.json [--overlay check.mp4]
"""
import argparse
import json

import cv2
import mediapipe as mp
import numpy as np


def red_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (0, 110, 50), (9, 255, 255)) | cv2.inRange(hsv, (168, 110, 50), (180, 255, 255))


def iou(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter + 1e-6)


def pick(frame, boxes, prev):
    """Score = share of the frame's red-torso pixels (she is the one in the big red corset) + continuity."""
    reds = []
    for b in boxes:
        x0, y0, x1, y1 = [int(v) for v in b]
        h, w = y1 - y0, x1 - x0
        torso = frame[y0 + int(h * 0.15):y0 + int(h * 0.5), x0 + int(w * 0.2):x1 - int(w * 0.2)]
        reds.append(float(red_mask(torso).sum() / 255) if torso.size else 0.0)
    top = max(reds) or 1.0
    best, score = None, -1.0
    for b, r in zip(boxes, reds):
        s = r / top + (0.5 * iou(b, prev) if prev is not None else 0)
        if s > score:
            best, score = b, s
    return best, score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--end", type=float, default=1e9)
    ap.add_argument("--out", required=True)
    ap.add_argument("--overlay")
    ap.add_argument("--yolo", default="yolov8m.pt")
    a = ap.parse_args()
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.set(cv2.CAP_PROP_POS_MSEC, a.start * 1000)
    from ultralytics import YOLO
    det = YOLO(a.yolo)
    pose = mp.solutions.pose.Pose(static_image_mode=True, model_complexity=2, smooth_landmarks=True,
                                  min_detection_confidence=0.4, min_tracking_confidence=0.4)
    writer = None
    frames, prev = [], None
    while True:
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        ok, f = cap.read()
        if not ok or t > a.end:
            break
        H, W = f.shape[:2]
        boxes = [b.xyxy[0].tolist() for b in det(f, classes=[0], conf=0.3, verbose=False)[0].boxes]
        box, sc = pick(f, boxes, prev) if boxes else (None, 0)
        r = None
        if box is not None and sc > 0.5:
            prev = box
            # keep only her: copy her (slightly padded) box onto a neutral square canvas so neighbours vanish
            bw, bh = box[2] - box[0], box[3] - box[1]
            bx0, by0 = int(max(box[0] - bw * 0.06, 0)), int(max(box[1] - bh * 0.04, 0))
            bx1, by1 = int(min(box[2] + bw * 0.06, W)), int(min(box[3] + bh * 0.04, H))
            side = int(max(bx1 - bx0, by1 - by0) * 1.15)
            crop = np.full((side, side, 3), 110, np.uint8)
            ox, oy = (side - (bx1 - bx0)) // 2, (side - (by1 - by0)) // 2
            crop[oy:oy + by1 - by0, ox:ox + bx1 - bx0] = f[by0:by1, bx0:bx1]
            x0, y0, x1, y1 = bx0 - ox, by0 - oy, bx0 - ox + side, by0 - oy + side
            r = pose.process(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
        rec = {"t": round(t - a.start, 4), "ok": bool(r and r.pose_world_landmarks)}
        if rec["ok"]:
            rec["world"] = [[round(l.x, 4), round(l.y, 4), round(l.z, 4)] for l in r.pose_world_landmarks.landmark]
            rec["vis"] = [round(l.visibility, 3) for l in r.pose_world_landmarks.landmark]
            rec["img"] = [[round(x0 + l.x * (x1 - x0), 1), round(y0 + l.y * (y1 - y0), 1)] for l in r.pose_landmarks.landmark]
            rec["box"] = [round(v, 1) for v in box]
        frames.append(rec)
        if a.overlay:
            if writer is None:
                writer = cv2.VideoWriter(a.overlay, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W // 2, H // 2))
            g = f.copy()
            if rec["ok"]:
                cv2.rectangle(g, (int(prev[0]), int(prev[1])), (int(prev[2]), int(prev[3])), (255, 255, 0), 3)
                for i, j in mp.solutions.pose.POSE_CONNECTIONS:
                    p, q = rec["img"][i], rec["img"][j]
                    cv2.line(g, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), (0, 255, 0), 4)
            writer.write(cv2.resize(g, (W // 2, H // 2)))
    if writer:
        writer.release()
    json.dump({"fps": fps, "start": a.start, "landmarks": "mediapipe_pose_33", "frames": frames}, open(a.out, "w"))
    ok = sum(fr["ok"] for fr in frames)
    print(f"{len(frames)} frames, {ok} with pose ({ok / max(len(frames), 1):.0%}) -> {a.out}")


if __name__ == "__main__":
    main()
