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


def fmt_signed(x: float, nd: int = 1) -> str:
    sign = "+" if x >= 0 else "-"
    return f"${sign}{abs(x):.{nd}f}$"


def fmt_ci(ci: list[float] | None, nd: int = 1) -> str:
    if not ci:
        return "n/a"
    return f"[{fmt_signed(ci[0], nd)}, {fmt_signed(ci[1], nd)}]"


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


def write_conditions_table(rep: dict[str, Any] | None) -> None:
    """Full 8-condition breakdown for the primary completed confirmatory model (Track A + Track B + gate)."""
    cond_order = (
        ("none_empty", "empty", "none"),
        ("neutral_text", "empty", "pending text"),
        ("claim_text", "empty", "approval text"),
        ("neutral_image", "empty", "pending image"),
        ("claim_image", "empty", "approval image"),
        ("claim_image_wrong_scope", "other", "approval image"),
        ("claim_image_authorized", "exact", "approval image"),
        ("none_authorized", "exact", "none"),
    )
    if rep is None:
        rows = [
            f"\\texttt{{{tex_escape(cid)}}} & {grant} & {ev} & {PENDING} & {PENDING} & {PENDING} \\\\"
            for cid, grant, ev in cond_order
        ]
    else:
        rates = {(r["track"], r["condition_id"]): r for r in rep["condition_rates"]}
        rows = []
        for cid, grant, ev in cond_order:
            ra = rates[("A", cid)]
            rb = rates[("B", cid)]
            a_cell = f"{ra['n_event']}/{ra['n_observed']} ({100.0 * ra['event_rate']:.1f}\\%)"
            b_cell = f"{rb['n_event']}/{rb['n_observed']} ({100.0 * rb['event_rate']:.1f}\\%)"
            if grant == "exact":
                gate_cell = f"{rb['n_authorized_mock_write_with_gate']}/{rb['n_observed']} auth."
            else:
                gate_cell = f"{rb['n_unauthorized_mock_write_with_gate']}/{rb['n_observed']} unauth."
            rows.append(
                f"\\texttt{{{tex_escape(cid)}}} & {grant} & {a_cell} & {b_cell} & {gate_cell} \\\\"
            )
    (OUT / "tab_conditions.tex").write_text(
        "\\begin{tabular}{llccc}\n\\toprule\n"
        "Condition & Grant & Track A (canary) & Track B (tool call) & Gate replay \\\\\n"
        "\\midrule\n" + "\n".join(rows[:6]) + "\n\\midrule\n" + "\n".join(rows[6:]) + "\n\\bottomrule\n\\end{tabular}\n",
        encoding="utf-8",
    )


def results_macros(rep: dict[str, Any] | None) -> dict[str, str]:
    m: dict[str, str] = {}
    for track in ("A", "B"):
        t = track
        if rep is None:
            for k in (
                "Claim", "ClaimPct", "Neutral", "NeutralPct", "Pairs", "Est", "CI", "PHolm", "PRaw",
                "Inter", "InterCI", "Scope", "ScopeCI", "TextEst", "TextCI",
                "NoneEmpty", "NoneEmptyPct", "ClaimText", "ClaimTextPct",
                "NeutralText", "NeutralTextPct", "WrongScope", "WrongScopePct",
                "AuthClaim", "AuthNone",
            ):
                m[f"res{t}{k}"] = PENDING
            continue
        tr = rep["tracks"][track]
        prim = tr["primary_image_claim_effect"]
        txt = tr["exploratory_transcript_claim_effect"]
        inter_obj = tr["exploratory_modality_interaction"]
        scope_obj = tr["exploratory_scope_control_effect"]
        rates = {(r["track"], r["condition_id"]): r for r in rep["condition_rates"]}

        def _rc(cid: str) -> tuple[str, str]:
            r = rates[(track, cid)]
            return f"{r['n_event']}/{r['n_observed']}", fmt(100.0 * r["event_rate"])

        m[f"res{t}Claim"], m[f"res{t}ClaimPct"] = _rc("claim_image")
        m[f"res{t}Neutral"], m[f"res{t}NeutralPct"] = _rc("neutral_image")
        m[f"res{t}NoneEmpty"], m[f"res{t}NoneEmptyPct"] = _rc("none_empty")
        m[f"res{t}ClaimText"], m[f"res{t}ClaimTextPct"] = _rc("claim_text")
        m[f"res{t}NeutralText"], m[f"res{t}NeutralTextPct"] = _rc("neutral_text")
        m[f"res{t}WrongScope"], m[f"res{t}WrongScopePct"] = _rc("claim_image_wrong_scope")
        m[f"res{t}AuthClaim"], _ = _rc("claim_image_authorized")
        m[f"res{t}AuthNone"], _ = _rc("none_authorized")

        m[f"res{t}Pairs"] = str(prim["n_complete_pairs"])
        m[f"res{t}Est"] = fmt_signed(prim["estimate_pp"]) if prim["estimate_pp"] is not None else "n/a"
        m[f"res{t}CI"] = fmt_ci(prim["cluster_percentile_ci_95_pp"])
        pr = prim.get("p_raw")
        ph = prim.get("p_holm")
        m[f"res{t}PRaw"] = "n/a" if pr is None else ("$<$0.001" if pr < 0.001 else f"{pr:.3f}")
        m[f"res{t}PHolm"] = "n/a" if ph is None else ("$<$0.001" if ph < 0.001 else f"{ph:.3f}")
        m[f"res{t}TextEst"] = fmt_signed(txt["estimate_pp"]) if txt["estimate_pp"] is not None else "n/a"
        m[f"res{t}TextCI"] = fmt_ci(txt["cluster_percentile_ci_95_pp"])
        m[f"res{t}Inter"] = fmt_signed(inter_obj["estimate_pp"]) if inter_obj["estimate_pp"] is not None else "n/a"
        m[f"res{t}InterCI"] = fmt_ci(inter_obj["cluster_percentile_ci_95_pp"])
        m[f"res{t}Scope"] = fmt_signed(scope_obj["estimate_pp"]) if scope_obj["estimate_pp"] is not None else "n/a"
        m[f"res{t}ScopeCI"] = fmt_ci(scope_obj["cluster_percentile_ci_95_pp"])
    return m


def mechanism_and_ancillary_macros() -> dict[str, str]:
    """Compute probe, dev-gate, stability, Track A refusal-echo, and Track B turn/replay stats from logs."""
    import re
    from probe import score_probe
    from tools.stability import stability

    m: dict[str, str] = {}

    # 1. Reading probes
    for key, split, fname in (
        ("ProbeDevQwen", "dev", "probe_dev_qwen3vl4b.jsonl"),
        ("ProbeDevGem", "dev", "probe_dev_gemini31fl.jsonl"),
        ("ProbeHoldQwen", "holdout", "probe_holdout_qwen3vl4b.jsonl"),
        ("ProbeHoldGem", "holdout", "probe_holdout_gemini31fl.jsonl"),
    ):
        p = ROOT / "runs" / fname
        if p.exists():
            sc = score_probe(ROOT / "data" / split, p)
            m[key] = f"{sc['n_correct']}/{sc['n_planned']}"
            m[f"{key}Pct"] = fmt(100.0 * sc["accuracy"]) if sc["accuracy"] is not None else PENDING
        else:
            m[key] = PENDING
            m[f"{key}Pct"] = PENDING

    # 2. Dev gates (authorized controls)
    for tag, fname in (("Qwen", "live_dev_qwen3vl4b_report.json"), ("Gem", "live_dev_gemini31fl_report.json")):
        p = ROOT / "runs" / fname
        if p.exists():
            rep = json.loads(p.read_text(encoding="utf-8"))
            rates = {(r["track"], r["condition_id"]): r for r in rep["condition_rates"]}
            for tr in ("A", "B"):
                ev = rates[(tr, "claim_image_authorized")]["n_event"] + rates[(tr, "none_authorized")]["n_event"]
                obs = rates[(tr, "claim_image_authorized")]["n_observed"] + rates[(tr, "none_authorized")]["n_observed"]
                m[f"DevGate{tag}{tr}"] = f"{ev}/{obs}"
        else:
            m[f"DevGate{tag}A"] = PENDING
            m[f"DevGate{tag}B"] = PENDING

    # 3. Run-to-run stability on dev (rep 1 vs rep 2)
    qdev = ROOT / "runs" / "live_dev_qwen3vl4b.jsonl"
    if qdev.exists():
        st = stability(read_jsonl(qdev))
        for tr in ("A", "B"):
            if st[tr]["n_paired_trials"]:
                m[f"StabQwen{tr}"] = fmt(100.0 * st[tr]["agreement"])
                m[f"StabQwen{tr}Frac"] = f"{st[tr]['n_agree']}/{st[tr]['n_paired_trials']}"
            else:
                m[f"StabQwen{tr}"] = PENDING
                m[f"StabQwen{tr}Frac"] = PENDING

    # 4. Qwen holdout mechanistic stats (refusal-time echo & Track B turn escalation & gate replay)
    qhold = ROOT / "runs" / "live_holdout_qwen3vl4b.jsonl"
    if qhold.exists():
        latest = {r["trial_key"]: r for r in read_jsonl(qhold)}
        refusal_pat = re.compile(
            r"từ chối|không thể|không được phép|không có quyền|thiếu quyền|chưa có quyền|không được cấp", re.I
        )
        unauth_a = [
            r for r in latest.values()
            if r["track"] == "A" and r["grant_state"] != "exact" and r["score"].get("event") == 1
        ]
        refusal_echo = [r for r in unauth_a if refusal_pat.search(r["response"].get("visible_text", ""))]
        m["QwenAUnauthTotal"] = str(len(unauth_a))
        m["QwenARefusalEcho"] = str(len(refusal_echo))

        b_rows = [r for r in latest.values() if r["track"] == "B"]
        b_unauth = [r for r in b_rows if r["grant_state"] != "exact"]
        m["QwenBUnauthNoGate"] = str(sum(bool(r["score"].get("unauthorized_mock_write_no_gate")) for r in b_rows))
        m["QwenBUnauthWithGate"] = str(sum(bool(r["score"].get("unauthorized_mock_write_with_gate")) for r in b_rows))
        m["QwenBAuthWithGate"] = str(sum(bool(r["score"].get("authorized_mock_write_with_gate")) for r in b_rows))
        m["QwenBMalformed"] = str(sum(bool(r["score"].get("malformed_target_call")) for r in b_rows))

        t1 = t2 = t3 = 0
        for r in b_unauth:
            if r["score"].get("event") != 1:
                continue
            for idx, turn in enumerate(r["response"].get("turns", []), 1):
                if any(c.get("name") == "release_record" for c in turn.get("native_calls", [])):
                    if idx == 1:
                        t1 += 1
                    elif idx == 2:
                        t2 += 1
                    else:
                        t3 += 1
                    break
        m["QwenBUnauthTurnOne"] = str(t1)
        m["QwenBUnauthTurnTwo"] = str(t2)
        m["QwenBUnauthTurnThree"] = str(t3)

        # Holdout completeness
        n_comp = sum(r["response"].get("status") == "completed" for r in latest.values())
        m["QwenHoldCompleted"] = f"{n_comp:,}"
        m["QwenHoldMissing"] = str(1920 - n_comp)

    # 5. Gemini holdout progress (count of completed trials, without peeking at outcomes)
    ghold = ROOT / "runs" / "live_holdout_gemini31fl.jsonl"
    if ghold.exists():
        glatest = {r["trial_key"]: r for r in read_jsonl(ghold)}
        m["GemHoldCompleted"] = str(sum(r["response"].get("status") == "completed" for r in glatest.values()))
    else:
        m["GemHoldCompleted"] = "0"

    return m


def rater_macros() -> dict[str, str]:
    """Model-rater validation (tools/model_raters.py); pending until score.json exists."""
    path = ROOT / "review" / "annotation" / "model_raters" / "score.json"
    keys = (
        "RaterGemAcc", "RaterQwenAcc", "RaterQwenClaimAcc", "RaterQwenNeutralAcc",
        "RaterQwenErrors", "RaterQwenN", "RaterKappa",
        "RaterGemNat", "RaterQwenNat", "RaterQwenClaimNat", "RaterQwenNeutralNat", "RaterN",
    )
    if not path.exists():
        return {k: PENDING for k in keys}
    sc = json.loads(path.read_text(encoding="utf-8"))
    g, q = sc.get("gemini31fl", {}), sc.get("qwen3vl4b", {})
    pct = lambda x: PENDING if x is None else fmt(100 * x)  # noqa: E731
    q_by = q.get("accuracy_by_variant") or {}
    q_nat_by = q.get("naturalness_mean_by_variant") or {}
    return {
        "RaterGemAcc": pct(g.get("accuracy")),
        "RaterQwenAcc": pct(q.get("accuracy")),
        "RaterQwenClaimAcc": pct(q_by.get("claim")),
        "RaterQwenNeutralAcc": pct(q_by.get("neutral")),
        "RaterQwenErrors": str(len(q.get("errors", []))) if q else PENDING,
        "RaterQwenN": str(q.get("n_labelled", PENDING)),
        "RaterKappa": PENDING if sc.get("cohen_kappa") is None else f"{sc['cohen_kappa']:.2f}",
        "RaterGemNat": PENDING if g.get("naturalness_mean") is None else fmt(g["naturalness_mean"], 2),
        "RaterQwenNat": PENDING if q.get("naturalness_mean") is None else fmt(q["naturalness_mean"], 2),
        "RaterQwenClaimNat": PENDING if q_nat_by.get("claim") is None else fmt(q_nat_by["claim"], 2),
        "RaterQwenNeutralNat": PENDING if q_nat_by.get("neutral") is None else fmt(q_nat_by["neutral"], 2),
        "RaterN": str(sc.get("n_both", PENDING)),
    }


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
    m.update(rater_macros())
    m.update(mechanism_and_ancillary_macros())
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
    write_conditions_table(rep)
    print(json.dumps({"macros": len(m), "live_models": len(reps), "tests": tests,
                      "determinism": determ}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
