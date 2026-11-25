"""Stage-design catalogue: every kit validates, cross-references hold, and generated files are current."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
STAGES = ROOT / "content" / "stages"
SCHEMA = json.loads((ROOT / "schema" / "stage-design.v1.schema.json").read_text())
INDEX = json.loads((STAGES / "index.json").read_text())
DESIGNS = [json.loads((STAGES / d["spec"]).read_text()) for d in INDEX["designs"]]


def test_three_designs_per_venue():
    for v in INDEX["venues"]:
        assert len(v["stageKits"]) == 3, v["venueId"]


@pytest.mark.parametrize("doc", DESIGNS, ids=lambda d: d["stageKit"])
def test_design_valid(doc):
    Draft202012Validator(SCHEMA).validate(doc)
    venue = next(v for v in INDEX["venues"] if v["venueId"] == doc["venueId"])
    assert venue["tier"] == doc["tier"]
    ids = [e["id"] for e in doc["elements"]]
    assert len(ids) == len(set(ids)), "duplicate element id"
    fx_ids = {f["id"] for f in doc["fx"]}
    assert set(doc["cueTargets"]["pyroPositions"]) <= fx_ids
    assert set(doc["cueTargets"]["kinetics"]) <= set(ids)
    marks = [m["id"] for m in doc["marks"]]
    assert "center" in marks and len(marks) == len(set(marks))
    assert (STAGES / doc["tier"] / f'{doc["stageKit"]}.svg').exists()
    if doc["tier"] in ("club", "theater"):  # indoor small rooms: no open flame
        assert not any("flame" in f["effects"] for f in doc["fx"])


def test_stage_kits_unique():
    kits = [d["stageKit"] for d in DESIGNS]
    assert len(kits) == len(set(kits))


def test_generated_files_current(tmp_path):
    before = {p: p.read_bytes() for p in STAGES.rglob("*") if p.is_file()}
    subprocess.run([sys.executable, str(ROOT / "pipeline" / "tools" / "stage_designs.py")], check=True, capture_output=True)
    after = {p: p.read_bytes() for p in STAGES.rglob("*") if p.is_file()}
    assert before == after, "content/stages is stale: run pipeline/tools/stage_designs.py"
