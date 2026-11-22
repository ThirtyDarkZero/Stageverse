"""Validate a StageVerse show package folder.

Two layers:
1. JSON Schema validation of show.json, the analysis file and the cue timeline.
2. Cross-file checks the schemas cannot express: referenced files exist,
   checksums match, analysis is ordered and fits the song, and every cue
   resolves to a time inside the show.

The same rules are mirrored by the Unreal loader (ShowRuntime) and the backend,
so a package that passes here plays everywhere.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schema"
SCHEMA_FILES = {
    "show": "show-package.v1.schema.json",
    "cues": "cue-timeline.v1.schema.json",
    "beats": "beats.v1.schema.json",
}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


@lru_cache(maxsize=None)
def validator(kind: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_DIR / SCHEMA_FILES[kind]).read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _schema_errors(kind: str, doc: Any, label: str, report: Report) -> None:
    for err in sorted(validator(kind).iter_errors(doc), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in err.absolute_path) or "(root)"
        report.error(f"{label}: {where}: {err.message}")


def _load_json(path: Path, label: str, report: Report) -> Any | None:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        report.error(f"{label}: file not found: {path.name}")
    except json.JSONDecodeError as exc:
        report.error(f"{label}: invalid JSON: {exc}")
    return None


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def referenced_paths(show: dict) -> list[str]:
    paths = [show["audio"]["master"], *show["audio"]["stems"].values(), show["analysis"], show["cues"]]
    for p in show["performers"]:
        paths.append(p["body"])
        if "face" in p:
            paths.append(p["face"])
    return paths


def beat_ms(bpm: float) -> float:
    return 60000.0 / bpm


def resolve_cue_ms(cue: dict, analysis: dict) -> int:
    """Resolve a cue's anchor to milliseconds. Raises IndexError for a bad anchor."""
    if "t" in cue:
        base = cue["t"]
    elif "beat" in cue:
        base = analysis["beats"][cue["beat"]]
    else:
        sec = analysis["sections"][cue["section"]["index"]]
        base = sec["endMs"] if cue["section"].get("at") == "end" else sec["startMs"]
    return round(base + cue.get("offsetBeats", 0) * beat_ms(analysis["bpm"]))


def _check_analysis(analysis: dict, duration_ms: int, report: Report) -> None:
    beats = analysis["beats"]
    if any(b2 <= b1 for b1, b2 in zip(beats, beats[1:])):
        report.error("analysis: beats must be strictly ascending")
    if beats and beats[-1] > duration_ms:
        report.error(f"analysis: last beat {beats[-1]} ms is after the show ends ({duration_ms} ms)")
    missing = set(analysis["downbeats"]) - set(beats)
    if missing:
        report.error(f"analysis: {len(missing)} downbeats are not in beats[], e.g. {min(missing)}")
    prev_end = 0
    for i, sec in enumerate(analysis["sections"]):
        if sec["endMs"] <= sec["startMs"]:
            report.error(f"analysis: sections/{i} ends before it starts")
        if sec["startMs"] < prev_end:
            report.error(f"analysis: sections/{i} overlaps the previous section")
        if sec["endMs"] > duration_ms:
            report.error(f"analysis: sections/{i} runs past the end of the show")
        prev_end = sec["endMs"]


def _check_cues(cues: dict, analysis: dict, duration_ms: int, report: Report) -> None:
    for ti, track in enumerate(cues["tracks"]):
        for ci, cue in enumerate(track["cues"]):
            where = f"cues: tracks/{ti}({track['type']})/cues/{ci}"
            try:
                ms = resolve_cue_ms(cue, analysis)
            except IndexError:
                report.error(f"{where}: anchor points past the end of the analysis data")
                continue
            if "section" in cue and "label" in cue["section"]:
                actual = analysis["sections"][cue["section"]["index"]]["label"]
                if actual != cue["section"]["label"]:
                    report.error(
                        f"{where}: section {cue['section']['index']} is '{actual}', cue says '{cue['section']['label']}'"
                    )
            if not 0 <= ms <= duration_ms:
                report.error(f"{where}: resolves to {ms} ms, outside 0..{duration_ms}")


def validate_package(root: str | Path, check_files: bool = True) -> Report:
    """Validate the package at `root`. With check_files=False, missing media files are not errors."""
    root = Path(root)
    report = Report()

    show = _load_json(root / "show.json", "show.json", report)
    if show is None:
        return report
    _schema_errors("show", show, "show.json", report)
    if report.errors:
        return report  # cross-file checks assume a well-formed manifest

    ids = [p["performerId"] for p in show["performers"]]
    if len(ids) != len(set(ids)):
        report.error("show.json: performerId values must be unique")

    for rel in referenced_paths(show):
        f = root / rel
        if not f.is_file():
            (report.error if check_files else report.warn)(f"file not found: {rel}")
            continue
        expected = show.get("checksums", {}).get(rel)
        if expected is None:
            report.warn(f"no checksum for {rel}")
        elif sha256_of(f) != expected:
            report.error(f"checksum mismatch: {rel}")

    analysis = _load_json(root / show["analysis"], "analysis", report)
    cues = _load_json(root / show["cues"], "cues", report)
    if analysis is not None:
        _schema_errors("beats", analysis, "analysis", report)
    if cues is not None:
        _schema_errors("cues", cues, "cues", report)
    if report.errors or analysis is None or cues is None:
        return report

    _check_analysis(analysis, show["durationMs"], report)
    _check_cues(cues, analysis, show["durationMs"], report)
    return report
