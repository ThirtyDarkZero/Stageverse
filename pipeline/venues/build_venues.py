"""Build venue blockouts: FBX per part, markers.json, seats.json, previews.

Usage (Blender 4.2+ or the `bpy` wheel, Python 3.11):
    blender -b -P pipeline/venues/build_venues.py -- [arena|theater|all] [--no-render]
    python pipeline/venues/build_venues.py [arena|theater|all] [--no-render]

Outputs go to unreal/SourceArt/Venues/<Venue>/.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "unreal", "SourceArt", "Venues")

import venuekit as vk  # noqa: E402
import plan  # noqa: E402


def run(module, render=True):
    v, meta = module.build()
    out = os.path.join(OUT, v.name)
    files = v.export(out)
    plan.draw_plan(os.path.join(out, "markers.json"), os.path.join(out, "seats.json"),
                   os.path.join(out, "previews", f"{v.name}_plan_diagram.png"))
    if render:
        vk.render_views(v, os.path.join(out, "previews"), module.VIEWS,
                        hide_parts=getattr(module, "HIDE_IN_PREVIEW", ("Roof",)))
    print(v.name, v.capacity)
    for f in files:
        print("  ", f["file"], f["tris"], "tris")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    which = next((a for a in argv if not a.startswith("-")), "all")
    render = "--no-render" not in argv
    if which in ("arena", "all"):
        import arena
        run(arena, render)
    if which in ("theater", "all"):
        import theater
        run(theater, render)


if __name__ == "__main__":
    main()
