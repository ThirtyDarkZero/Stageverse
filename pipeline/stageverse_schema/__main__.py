"""CLI: python -m stageverse_schema validate <package-dir> [--schema-only]"""

import argparse
import sys

from .validate import validate_package


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stageverse_schema")
    sub = parser.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="validate a show package folder")
    v.add_argument("package", help="path to the package folder (contains show.json)")
    v.add_argument(
        "--schema-only",
        action="store_true",
        help="treat missing media files as warnings (for examples without audio or motion)",
    )
    args = parser.parse_args(argv)

    report = validate_package(args.package, check_files=not args.schema_only)
    for w in report.warnings:
        print(f"warning: {w}")
    for e in report.errors:
        print(f"error: {e}")
    print("OK" if report.ok else f"FAILED ({len(report.errors)} errors)")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
