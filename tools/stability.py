"""Run-to-run stability of a model under the VAS protocol (issue I-008).

Provider APIs are not fully deterministic even at temperature 0. The protocol runs the
development split twice (replicate 1 and replicate 2, different shuffles) and reports how
often the scored event agrees between the two runs. This is descriptive and does not enter
the confirmatory analysis.

    python experiment.py run --backend openai --live --data data/dev --out runs/live_dev.jsonl --replicate 2
    python tools/stability.py --log runs/live_dev.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dataset import read_jsonl  # noqa: E402
from experiment import MEASURED  # noqa: E402


def stability(rows: list[dict]) -> dict:
    latest: dict[tuple[int, str], dict] = {}
    for r in rows:
        key = r["trial_key"].rsplit("::rep", 1)[0]
        latest[(int(r.get("replicate", 1)), key)] = r
    keys = {k for (_, k) in latest}
    out: dict = {}
    for track in ("A", "B"):
        agree = total = 0
        disagree_conditions: dict[str, int] = {}
        for k in keys:
            a, b = latest.get((1, k)), latest.get((2, k))
            if not a or not b or a["track"] != track:
                continue
            if a["response"]["status"] not in MEASURED or b["response"]["status"] not in MEASURED:
                continue
            total += 1
            if a["score"].get("event") == b["score"].get("event"):
                agree += 1
            else:
                disagree_conditions[a["condition_id"]] = disagree_conditions.get(a["condition_id"], 0) + 1
        out[track] = {
            "n_paired_trials": total,
            "n_agree": agree,
            "agreement": round(agree / total, 4) if total else None,
            "disagreements_by_condition": disagree_conditions,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(stability(read_jsonl(args.log)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
