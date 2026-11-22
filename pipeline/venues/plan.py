"""Top-down plan diagram of a venue from its markers.json + seats.json."""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402

TIER_COLOR = {"lower": "#b03a48", "upper": "#3a5aa0", "floor_ga": "#8a8a8a",
              "balcony": "#8e44ad", "gallery": "#c0729a"}


def draw_plan(markers_path, seats_path, out_png):
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    M = json.load(open(markers_path))
    S = json.load(open(seats_path))
    fig, ax = plt.subplots(figsize=(16, 11), dpi=110)
    ax.set_aspect("equal")
    ax.set_facecolor("#f4f2ee")
    for sec in S["sections"]:
        col = TIER_COLOR.get(sec["tier"], "#555")
        xs = [s[0] / 100 for s in sec["seats"]]
        ys = [-s[1] / 100 for s in sec["seats"]]
        cs = [col if s[5] == 0 else ("#e8a33d" if s[5] == 1 else "#cfcfcf") for s in sec["seats"]]
        ax.scatter(xs, ys, s=0.6 if sec["tier"] != "floor_ga" else 1.2, c=cs, linewidths=0)
        if xs and sec["tier"] != "floor_ga":
            ax.text(sum(xs) / len(xs), sum(ys) / len(ys), sec["id"], fontsize=6, ha="center", va="center",
                    color="black", alpha=0.8)
    for m in M["markers"]:
        x, y, _ = m["loc_m"]
        t = m["type"]
        if t in ("stage_zone", "crowd_zone"):
            sx, sy, _ = m["size_m"]
            if m.get("shape") == "disc":
                ax.add_patch(Circle((x, y), sx / 2, fill=t == "stage_zone", fc="#222", ec="#222", alpha=0.8))
            else:
                ax.add_patch(Rectangle((x - sx / 2, y - sy / 2), sx, sy, fill=t == "stage_zone",
                                       fc="#222" if t == "stage_zone" else "none",
                                       ec="#222" if t == "stage_zone" else "#2a8a4a",
                                       ls="-" if t == "stage_zone" else "--", alpha=0.75, lw=1))
            ax.text(x, y, m["id"].replace("Zone_", ""), fontsize=6,
                    color="white" if t == "stage_zone" else "#1d5e33", ha="center", va="center")
        elif t == "rig_grid":
            ax.plot(x, y, "+", ms=2.5, color="#a08a20", alpha=0.6)
        elif t == "rig_point":
            ax.plot(x, y, "s", ms=3.5, color="#d4a017")
        elif t == "camera":
            ax.plot(x, y, "^", ms=6, color="#1f8f5f")
            ax.text(x, y + 1.2, m["id"].replace("Cam_", ""), fontsize=5.5, color="#1f8f5f", ha="center")
        elif t == "performer_mark":
            ax.plot(x, y, "o", ms=3, color="#ff4f9a")
        elif t == "fx_point":
            ax.plot(x, y, "*", ms=4, color="#ff6a00")
        elif t == "vomitory":
            ax.plot(x, y, "D", ms=3, color="#444")
    cap = M.get("capacity", {})
    lines = [M["title"]] + [f"{k}: {v}" for k, v in cap.items()]
    ax.text(0.01, 0.99, "\n".join(lines), transform=ax.transAxes, fontsize=8, va="top",
            family="monospace", bbox=dict(fc="white", ec="#999", alpha=0.9))
    legend = ("seats: tier colour = sold, orange = limited view, grey = not sold end-stage | "
              "squares = rig points, + = roof grid, triangles = cameras, pink = performer marks, "
              "stars = FX, diamonds = vomitories | stage at left (-X), 1 grid line = 10 m")
    ax.set_title(legend, fontsize=7)
    ax.grid(True, color="#ddd", lw=0.5)
    ax.set_xticks(range(-80, 81, 10))
    ax.set_yticks(range(-70, 71, 10))
    ax.autoscale()
    ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)
