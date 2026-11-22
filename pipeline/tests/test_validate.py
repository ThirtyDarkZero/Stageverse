import copy
import json
import shutil
from pathlib import Path

import pytest

from stageverse_schema import resolve_cue_ms, validate_package
from stageverse_schema.validate import referenced_paths, sha256_of

EXAMPLE = Path(__file__).resolve().parents[2] / "schema" / "examples" / "arizona-rae-demo"


@pytest.fixture
def pkg(tmp_path: Path) -> Path:
    """A complete package: the example plus dummy media files and checksums."""
    root = tmp_path / "pkg"
    shutil.copytree(EXAMPLE, root)
    show = json.loads((root / "show.json").read_text())
    for rel in referenced_paths(show):
        f = root / rel
        if not f.exists():
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b"dummy " + rel.encode())
    show["checksums"] = {rel: sha256_of(root / rel) for rel in referenced_paths(show)}
    (root / "show.json").write_text(json.dumps(show))
    return root


def edit(root: Path, rel: str, fn) -> None:
    p = root / rel
    doc = json.loads(p.read_text())
    fn(doc)
    p.write_text(json.dumps(doc))
    if rel != "show.json":  # keep the manifest's checksum in step with the edit
        edit(root, "show.json", lambda s: s["checksums"].update({rel: sha256_of(p)}))


def test_example_validates_schema_only():
    report = validate_package(EXAMPLE, check_files=False)
    assert report.ok, report.errors


def test_complete_package_has_no_errors_or_warnings(pkg):
    report = validate_package(pkg)
    assert report.ok, report.errors
    assert report.warnings == []


def test_missing_media_is_an_error_by_default():
    report = validate_package(EXAMPLE)
    assert any("file not found: audio/master.ogg" in e for e in report.errors)


def test_performer_without_consent_is_rejected(pkg):
    edit(pkg, "show.json", lambda s: s["performers"][0].update(consentIds=[]))
    report = validate_package(pkg)
    assert not report.ok
    assert any("consentIds" in e for e in report.errors)


def test_ai_disclosure_is_required(pkg):
    edit(pkg, "show.json", lambda s: s["rights"].update(aiDisclosure=False))
    assert not validate_package(pkg).ok


@pytest.mark.parametrize("bad", ["../secrets.txt", "/etc/passwd", "a/../../b.ogg"])
def test_paths_cannot_escape_the_package(pkg, bad):
    edit(pkg, "show.json", lambda s: s["audio"].update(master=bad))
    assert not validate_package(pkg).ok


def test_checksum_mismatch(pkg):
    (pkg / "audio/master.ogg").write_bytes(b"tampered")
    report = validate_package(pkg)
    assert "checksum mismatch: audio/master.ogg" in report.errors


def test_cue_must_have_exactly_one_anchor(pkg):
    def two_anchors(c):
        c["tracks"][0]["cues"][0]["t"] = 0  # already has a section anchor
    edit(pkg, "cues/timeline.json", two_anchors)
    assert not validate_package(pkg).ok


def test_known_cue_type_requires_its_params(pkg):
    edit(pkg, "cues/timeline.json", lambda c: c["tracks"][0]["cues"][0].pop("shot"))
    report = validate_package(pkg)
    assert any("shot" in e for e in report.errors)


def test_unknown_cue_types_are_allowed(pkg):
    def add(c):
        c["tracks"].append({"type": "lasers", "cues": [{"beat": 4, "pattern": "fan", "speed": 2}]})
    edit(pkg, "cues/timeline.json", add)
    assert validate_package(pkg).ok


def test_beat_anchor_past_analysis_is_rejected(pkg):
    edit(pkg, "cues/timeline.json", lambda c: c["tracks"].append({"type": "lasers", "cues": [{"beat": 99999}]}))
    report = validate_package(pkg)
    assert any("past the end of the analysis" in e for e in report.errors)


def test_section_label_must_match(pkg):
    edit(pkg, "cues/timeline.json", lambda c: c["tracks"][0]["cues"][0]["section"].update(label="chorus"))
    report = validate_package(pkg)
    assert any("is 'intro', cue says 'chorus'" in e for e in report.errors)


def test_cue_after_show_end_is_rejected(pkg):
    edit(pkg, "cues/timeline.json", lambda c: c["tracks"][2]["cues"].append({"t": 10_000_000, "content": "x"}))
    report = validate_package(pkg)
    assert any("outside 0..180000" in e for e in report.errors)


def test_overlapping_sections_are_rejected(pkg):
    edit(pkg, "analysis/beats.json", lambda a: a["sections"][1].update(startMs=a["sections"][0]["startMs"]))
    report = validate_package(pkg)
    assert any("overlaps" in e for e in report.errors)


def test_resolve_cue_ms():
    analysis = {"bpm": 120, "beats": [0, 500, 1000, 1500], "sections": [{"label": "intro", "startMs": 0, "endMs": 2000}]}
    assert resolve_cue_ms({"t": 1234}, analysis) == 1234
    assert resolve_cue_ms({"beat": 2}, analysis) == 1000
    assert resolve_cue_ms({"beat": 2, "offsetBeats": -0.5}, analysis) == 750
    assert resolve_cue_ms({"section": {"index": 0, "at": "end"}}, analysis) == 2000
    with pytest.raises(IndexError):
        resolve_cue_ms({"beat": 4}, analysis)


def test_example_is_up_to_date(tmp_path):
    """The committed example must match what tools/make_example.py generates."""
    before = {p.relative_to(EXAMPLE): p.read_text() for p in EXAMPLE.rglob("*.json")}
    import runpy

    runpy.run_path(str(Path(__file__).resolve().parents[1] / "tools" / "make_example.py"))
    after = {p.relative_to(EXAMPLE): p.read_text() for p in EXAMPLE.rglob("*.json")}
    assert before == after


def test_timestamps_must_be_rfc3339(pkg):
    edit(pkg, "show.json", lambda s: s.update(createdAt="last tuesday"))
    assert not validate_package(pkg).ok
