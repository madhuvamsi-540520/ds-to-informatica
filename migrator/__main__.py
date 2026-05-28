"""CLI entrypoint: python -m migrator <command> [options]"""

import argparse
import json
import sys
from migrator.core import dsx_parser
from migrator.accelerators import (
    acc01_classifier, acc03_parameters, acc04_connections,
    acc06_scorer, acc07_naming
)


def cmd_run(args):
    """Run all Phase 1 rule-based accelerators against a DSX export."""
    print(f"Parsing DSX: {args.dsx}")
    export = dsx_parser.parse(args.dsx)
    print(f"  Found {len(export.jobs)} jobs, {len(export.parameter_sets)} parameter sets, {len(export.connections)} connections")

    print("\n[ACC-01] Classifying stages...")
    rows = acc01_classifier.classify(export, f"{args.output}/acc01_classification.csv")
    print(f"  → {len(rows)} stages classified")

    print("[ACC-03] Migrating parameter sets...")
    params = acc03_parameters.migrate(export, f"{args.output}/acc03_parameters")
    print(f"  → {len(params)} parameter sets exported")

    print("[ACC-04] Mapping connections...")
    conns = acc04_connections.migrate(export, f"{args.output}/acc04_connections")
    print(f"  → {len(conns)} connections mapped")

    print("[ACC-06] Scoring job complexity...")
    scores = acc06_scorer.score_all(export, f"{args.output}/acc06_scoring")
    complex_jobs = [s for s in scores if s["requires_claude_review"]]
    print(f"  → {len(scores)} jobs scored, {len(complex_jobs)} flagged for Claude review")

    print("[ACC-07] Transforming naming conventions...")
    names = acc07_naming.transform_all(export, f"{args.output}/acc07_naming")
    changed = [n for n in names if n["changed"]]
    print(f"  → {len(names)} names processed, {len(changed)} renamed")

    print(f"\nPhase 1 complete. Outputs in: {args.output}/")
    print("Run Claude API accelerators (ACC-02, 05, 08, 09, 10) for complex jobs.")


def cmd_acc01(args):
    export = dsx_parser.parse(args.dsx)
    rows = acc01_classifier.classify(export)
    print(json.dumps(rows, indent=2))


def cmd_acc06(args):
    export = dsx_parser.parse(args.dsx)
    scores = acc06_scorer.score_all(export)
    print(json.dumps(scores, indent=2))


def main():
    parser = argparse.ArgumentParser(
        prog="migrator",
        description="IBM DataStage → Informatica IDMC CDI Migration Toolkit"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run: full Phase 1 pipeline
    run_p = sub.add_parser("run", help="Run all Phase 1 accelerators")
    run_p.add_argument("--dsx", required=True, help="Path to DSX export file")
    run_p.add_argument("--output", default="output", help="Output directory")
    run_p.set_defaults(func=cmd_run)

    # acc01
    p = sub.add_parser("acc01", help="Stage classifier only")
    p.add_argument("--dsx", required=True)
    p.set_defaults(func=cmd_acc01)

    # acc06
    p = sub.add_parser("acc06", help="Complexity scorer only")
    p.add_argument("--dsx", required=True)
    p.set_defaults(func=cmd_acc06)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
