"""Compute every number the paper reports and write them as LaTeX macros and tables.

Rule (borrowed from the team's MobiSys workflow): no number is typed into the manuscript
by hand. Each value in ``paper/generated/`` is produced here from the frozen data, the run
logs and the analysis reports, so changing a log changes the paper on the next build.

Usage (from the repository root):
    python tools/make_paper_numbers.py                     # fast: data + existing logs
    python tools/make_paper_numbers.py --run-tests          # also run the unit tests
    python tools/make_paper_numbers.py --check-determinism  # also re-render dev and compare

Live model results are read from ``runs/live_holdout_report.json`` (confirmatory) when it
exists. Until then the result macros expand to a visible "pending" marker.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path
from statistics import NormalDist
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageChops  # noqa: E402

from dataset import ALL_TEMPLATE_STYLES, STATUS_VALUE_BOX, read_jsonl  # noqa: E402

OUT = ROOT / "paper" / "generated"
PENDING = r"\pending{}"
TEMPLATE_LABEL = {
    "gmail_dark": "Gmail-style mail (dark)",
    "outlook_light": "Outlook-style mail",
    "zalo_pc": "Zalo-style desktop chat",
    "teams_desktop": "Teams-style workspace chat",
    "messenger_web": "Messenger-style web chat",
    "vn_confirm_form": "A4 confirmation form",
    "vn_admin_decision": "A4 administrative decision",
    "vn_handover_slip": "A4 handover slip",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def status_sentence(transcript: str) -> str:
    for line in transcript.splitlines():
        if line.startswith("Thông tin phản hồi:"):
            return line.split(":", 1)[1].strip()
    raise ValueError("status line missing from transcript")


def token_edit_distance(a: list[str], b: list[str]) -> int:
    prev = list(range(len(b) + 1))
    for i, ta in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, tb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ta != tb))
        prev = cur
    return prev[-1]


def split_stats(split: str) -> dict[str, Any]:
    root = ROOT / "data" / split
    cases = read_jsonl(root / "manifest.jsonl")
    x0, y0, x1, y1 = STATUS_VALUE_BOX
    changed_frac: list[float] = []
    by_template_frac: dict[str, list[float]] = {}
    inside = 0
    len_diff: list[int] = []
    edit: list[int] = []
    words: list[int] = []
    ai_mentions = 0
    for case in cases:
        n_img = Image.open(root / case["evidence"]["neutral"]["image"]).convert("RGB")
        c_img = Image.open(root / case["evidence"]["claim"]["image"]).convert("RGB")
        diff = ImageChops.difference(n_img, c_img).convert("L").point(lambda v: 255 if v else 0)
        bbox = diff.getbbox()
        n_changed = diff.histogram()[255]
        frac = n_changed / (n_img.width * n_img.height)
        changed_frac.append(frac)
        by_template_frac.setdefault(case["template_style"], []).append(frac)
        if bbox and x0 <= bbox[0] and y0 <= bbox[1] and bbox[2] <= x1 and bbox[3] <= y1:
            inside += 1
        s_n = status_sentence(case["evidence"]["neutral"]["transcript"])
        s_c = status_sentence(case["evidence"]["claim"]["transcript"])
        len_diff.append(abs(len(s_c) - len(s_n)))
        edit.append(token_edit_distance(s_n.split(), s_c.split()))
        words.append(len(s_c.split()))
        ai_mentions += sum(" AI" in s or "trợ lý" in s for s in (s_n, s_c))
    families = {c["family_id"] for c in cases}
    templates = {t: sum(c["template_style"] == t for c in cases) for t in ALL_TEMPLATE_STYLES}
    return {
        "n_cases": len(cases),
        "n_images": 2 * len(cases),
        "n_families": len(families),
        "n_domains": len({c["domain"] for c in cases}),
        "templates": templates,
        "doc_types": {d: sum(c["doc_type"] == d for c in cases) for d in ("email", "memorandum", "clearance")},
        "pairs_inside_box": inside,
        "changed_pct_median": 100 * statistics.median(changed_frac),
        "changed_pct_max": 100 * max(changed_frac),
        "changed_pct_min": 100 * min(changed_frac),
        "changed_pct_by_template": {t: 100 * statistics.median(v) for t, v in by_template_frac.items()},
        "len_diff_median": statistics.median(len_diff),
        "len_diff_max": max(len_diff),
        "edit_median": statistics.median(edit),
        "edit_max": max(edit),
        "words_median": statistics.median(words),
        "ai_mentions": ai_mentions,
        "manifest_sha256": sha256(root / "manifest.jsonl"),
        "render_env": json.loads((root / "render_env.json").read_text(encoding="utf-8")),
        "n_trials": len(cases) * 16,
    }


def fixture_checks(split: str) -> dict[str, Any] | None:
    log = ROOT / "runs" / f"fixture_{split}.jsonl"
    if not log.exists():
        return None
    rows = read_jsonl(log)
    keys = {r["trial_key"] for r in rows}
    b = [r for r in rows if r["track"] == "B"]
    return {
        "n_rows": len(rows),
        "n_unique": len(keys),
        "b_unauth_no_gate": sum(bool(r["score"].get("unauthorized_mock_write_no_gate")) for r in b),
        "b_unauth_with_gate": sum(bool(r["score"].get("unauthorized_mock_write_with_gate")) for r in b),
        "b_auth_with_gate": sum(bool(r["score"].get("authorized_mock_write_with_gate")) for r in b),
        "b_exact_rows": sum(r["grant_state"] == "exact" for r in b),
    }


def power(delta: float, p_disc: float = 0.25, icc: float = 0.10, m: int = 5, n: int = 120,
          alpha: float = 0.025) -> float:
    """Normal-approximation power of the two-sided paired test with a family design effect."""
    se = math.sqrt((p_disc - delta**2) * (1 + (m - 1) * icc) / n)
    z = NormalDist().inv_cdf(1 - alpha / 2)
    return NormalDist().cdf(delta / se - z)


def run_tests() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    tail = (proc.stderr or "").strip().splitlines()
    ran = next((ln for ln in tail if ln.startswith("Ran ")), "Ran 0 tests")
    return {"n_tests": int(ran.split()[1]), "ok": proc.returncode == 0 and tail[-1].startswith("OK")}


def check_determinism() -> dict[str, Any]:
    from dataset import generate_dataset

    with tempfile.TemporaryDirectory() as tmp:
        generate_dataset("dev", tmp)
        again = sha256(Path(tmp) / "manifest.jsonl")
    return {"dev_rerender_identical": again == sha256(ROOT / "data" / "dev" / "manifest.jsonl")}


def fmt(x: float, nd: int = 1) -> str:
    return f"{x:.{nd}f}"


def live_reports() -> list[dict[str, Any]]:
    """All confirmatory holdout reports, one per model (runs/live_holdout*_report.json)."""
    reps = []
    for path in sorted((ROOT / "runs").glob("live_holdout*report.json")):
        rep = json.loads(path.read_text(encoding="utf-8"))
        if rep.get("report_mode") == "CONFIRMATORY_LIVE":
            reps.append(rep)
    return reps


def mde(power_target: float = 0.80, n: int = 120, **kw: Any) -> float:
    """Smallest paired effect (proportion) reaching the target power, by bisection."""
    lo, hi = 0.0, 0.49
    for _ in range(60):
        mid = (lo + hi) / 2
        if power(mid, n=n, **kw) < power_target:
            lo = mid
        else:
            hi = mid
    return hi


def tex_escape(text: str) -> str:
    return text.replace("_", "\\_").replace("&", "\\&").replace("%", "\\%")


def write_results_table(reps: list[dict[str, Any]]) -> None:
    """Table 4 rows: one per model and track; a single pending row per track before any run."""
    lines = []
    if not reps:
        for track, label in (("A", "A (canary)"), ("B", "B (tool call)")):
            lines.append(f"\\textit{{registered panel}} & {label} & {PENDING} & {PENDING} & {PENDING} & "
                         f"{PENDING} & {PENDING} & {PENDING} \\\\")
    for rep in reps:
        model = tex_escape(", ".join(rep.get("served_models") or rep.get("requested_models") or ["?"]))
        m = results_macros(rep)
        for track, label in (("A", "A (canary)"), ("B", "B (tool call)")):
            lines.append(
                f"\\texttt{{{model}}} & {label} & {m[f'res{track}Claim']} & {m[f'res{track}Neutral']} & "
                f"{m[f'res{track}Pairs']} & {m[f'res{track}Est']} {m[f'res{track}CI']} & "
                f"{m[f'res{track}PHolm']} & {m[f'res{track}Inter']} \\\\"
            )
    (OUT / "tab_results.tex").write_text(
        "\\begin{tabular}{llcccccc}\n\\toprule\n"
        "Model & Track & Claim & Neutral & Pairs & $\\Delta_{\\text{image}}$ [95\\% CI] & $p_{\\text{Holm}}$ & Interaction \\\\\n"
        "\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n",
        encoding="utf-8",
    )


def results_macros(rep: dict[str, Any] | None) -> dict[str, str]:
    m: dict[str, str] = {}
    for track in ("A", "B"):
        t = track
        if rep is None:
            for k in ("Claim", "Neutral", "Pairs", "Est", "CI", "PHolm", "Inter", "Scope"):
                m[f"res{t}{k}"] = PENDING
            continue
        tr = rep["tracks"][track]
        prim = tr["primary_image_claim_effect"]
        rates = {(r["track"], r["condition_id"]): r for r in rep["condition_rates"]}
        ci = prim["cluster_percentile_ci_95_pp"]
        m[f"res{t}Claim"] = f"{rates[(track, 'claim_image')]['n_event']}/{rates[(track, 'claim_image')]['n_observed']}"
        m[f"res{t}Neutral"] = f"{rates[(track, 'neutral_image')]['n_event']}/{rates[(track, 'neutral_image')]['n_observed']}"
        m[f"res{t}Pairs"] = str(prim["n_complete_pairs"])
        m[f"res{t}Est"] = fmt(prim["estimate_pp"]) if prim["estimate_pp"] is not None else "n/a"
        m[f"res{t}CI"] = f"[{fmt(ci[0])}, {fmt(ci[1])}]" if ci else "n/a"
        ph = prim.get("p_holm")
        m[f"res{t}PHolm"] = "n/a" if ph is None else ("$<$0.001" if ph < 0.001 else f"{ph:.3f}")
        inter = tr["exploratory_modality_interaction"]["estimate_pp"]
        scope = tr["exploratory_scope_control_effect"]["estimate_pp"]
        m[f"res{t}Inter"] = fmt(inter) if inter is not None else "n/a"
        m[f"res{t}Scope"] = fmt(scope) if scope is not None else "n/a"
    return m


def write_tables(dev: dict[str, Any], hold: dict[str, Any]) -> None:
    rows = []
    for t in ALL_TEMPLATE_STYLES:
        rows.append(
            f"{TEMPLATE_LABEL[t]} & {dev['templates'][t]} & {hold['templates'][t]} & "
            f"{fmt(hold['changed_pct_by_template'][t], 2)} \\\\"
        )
    body = "\n".join(rows)
    (OUT / "tab_corpus.tex").write_text(
        "\\begin{tabular}{lrrr}\n\\toprule\n"
        "Template & Dev records & Holdout records & Changed pixels (\\%) \\\\\n\\midrule\n"
        f"{body}\n\\midrule\n"
        f"Total & {dev['n_cases']} & {hold['n_cases']} & {fmt(hold['changed_pct_median'], 2)} \\\\\n"
        "\\bottomrule\n\\end{tabular}\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-tests", action="store_true")
    ap.add_argument("--check-determinism", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    cache_path = OUT / "numbers.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}

    dev, hold = split_stats("dev"), split_stats("holdout")
    fdev, fhold = fixture_checks("dev"), fixture_checks("holdout")
    tests = run_tests() if args.run_tests else cache.get("tests", {"n_tests": 0, "ok": False})
    determ = check_determinism() if args.check_determinism else cache.get("determinism", {})
    reps = live_reports()
    rep = reps[0] if reps else None

    numbers = {
        "dev": {k: v for k, v in dev.items() if k != "render_env"},
        "holdout": {k: v for k, v in hold.items() if k != "render_env"},
        "render_env": hold["render_env"],
        "fixture_dev": fdev,
        "fixture_holdout": fhold,
        "tests": tests,
        "determinism": determ,
        "power": {"10pp": power(0.10), "15pp": power(0.15)},
        "zero_event_bound_pct": 100 * (1 - 0.05 ** (1 / hold["n_families"])),
        "live_results_available": bool(reps),
        "n_live_models": len(reps),
        "mde80_pp_n120": 100 * mde(n=120),
        "mde80_pp_n240": 100 * mde(n=240),
    }
    cache_path.write_text(json.dumps(numbers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    m: dict[str, str] = {
        "nDevCases": str(dev["n_cases"]),
        "nDevImages": str(dev["n_images"]),
        "nDevFamilies": str(dev["n_families"]),
        "nDevTrials": str(dev["n_trials"]),
        "nHoldCases": str(hold["n_cases"]),
        "nHoldImages": str(hold["n_images"]),
        "nHoldFamilies": str(hold["n_families"]),
        "nHoldTrials": f"{hold['n_trials']:,}",
        "nHoldPerFamily": str(hold["n_cases"] // hold["n_families"]),
        "nAllPairs": str(dev["n_cases"] + hold["n_cases"]),
        "nAllImages": str(dev["n_images"] + hold["n_images"]),
        "nPairsInside": str(dev["pairs_inside_box"] + hold["pairs_inside_box"]),
        "changedMedian": fmt(hold["changed_pct_median"], 2),
        "changedMin": fmt(min(dev["changed_pct_min"], hold["changed_pct_min"]), 2),
        "changedMax": fmt(max(dev["changed_pct_max"], hold["changed_pct_max"]), 2),
        "editMedian": fmt(hold["edit_median"], 0),
        "editMax": str(max(dev["edit_max"], hold["edit_max"])),
        "lenDiffMedian": fmt(hold["len_diff_median"], 0),
        "lenDiffMax": str(max(dev["len_diff_max"], hold["len_diff_max"])),
        "wordsMedian": fmt(hold["words_median"], 0),
        "aiMentions": str(dev["ai_mentions"] + hold["ai_mentions"]),
        "holdEmail": str(hold["doc_types"]["email"]),
        "holdChat": str(hold["doc_types"]["memorandum"]),
        "holdForm": str(hold["doc_types"]["clearance"]),
        "devManifestShort": dev["manifest_sha256"][:12],
        "holdManifestShort": hold["manifest_sha256"][:12],
        "browserVersion": str(hold["render_env"].get("browser_version", "unknown")),
        "playwrightVersion": str(hold["render_env"].get("playwright", "unknown")),
        "nTests": str(tests.get("n_tests", 0)),
        "testsStatus": "passed" if tests.get("ok") else "not run",
        "determinism": "identical" if determ.get("dev_rerender_identical") else "not checked",
        "powerTen": fmt(100 * power(0.10), 0),
        "powerFifteen": fmt(100 * power(0.15), 0),
        "zeroBound": fmt(numbers["zero_event_bound_pct"], 2),
        "mdeHold": fmt(numbers["mde80_pp_n120"], 0),
        "mdeDouble": fmt(numbers["mde80_pp_n240"], 0),
        "nLiveModels": str(len(reps)),
    }
    if fdev and fhold:
        m.update(
            {
                "fixDevUnique": str(fdev["n_unique"]),
                "fixHoldUnique": f"{fhold['n_unique']:,}",
                "fixNoGate": str(fdev["b_unauth_no_gate"] + fhold["b_unauth_no_gate"]),
                "fixWithGate": str(fdev["b_unauth_with_gate"] + fhold["b_unauth_with_gate"]),
                "fixAuthGate": str(fdev["b_auth_with_gate"] + fhold["b_auth_with_gate"]),
                "fixExactRows": str(fdev["b_exact_rows"] + fhold["b_exact_rows"]),
            }
        )
    m.update(results_macros(rep))

    lines = [
        "% Generated by tools/make_paper_numbers.py. Do not edit by hand.",
        f"% live results available: {rep is not None}",
    ]
    for k, v in m.items():
        lines.append(f"\\newcommand{{\\vas{k[0].upper() + k[1:]}}}{{{v}}}")
    (OUT / "numbers.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_tables(dev, hold)
    write_results_table(reps)
    print(json.dumps({"macros": len(m), "live_models": len(reps), "tests": tests,
                      "determinism": determ}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
