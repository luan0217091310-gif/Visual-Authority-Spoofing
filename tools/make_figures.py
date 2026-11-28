"""Build the paper's figures from the frozen benchmark images.

fig_pairs.png : three matched pairs (mail, chat, A4 form). Each row shows the neutral and
                claim screenshots and, below them, the status region at full resolution, so
                the reader can see that only the status sentences differ.
fig_design.png/.pdf : the trial design (evidence channel vs. registry channel, two tracks,
                gate replay), drawn with Graphviz when `dot` is available.

Usage: python tools/make_figures.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dataset import read_jsonl  # noqa: E402

FIG = ROOT / "paper" / "figures"
CROP = (226, 360, 994, 462)  # status region in 1100x660 image coordinates (A4 tilt included)


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    for name in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def fig_pairs() -> Path:
    cases = {c["case_id"]: c for c in read_jsonl(ROOT / "data" / "holdout" / "manifest.jsonl")}
    picks = []
    for style in ("outlook_light", "teams_desktop", "vn_confirm_form"):
        picks.append(next(c for c in sorted(cases.values(), key=lambda c: c["case_id"])
                          if c["template_style"] == style))
    scale = 0.5
    full_w, full_h = int(1100 * scale), int(660 * scale)
    crop_w = CROP[2] - CROP[0]
    crop_h = CROP[3] - CROP[1]
    crop_scale = full_w / crop_w
    zoom_h = int(crop_h * crop_scale)
    pad, label_h, head_h = 16, 26, 40
    row_h = label_h + full_h + 6 + zoom_h + pad
    width = pad + 2 * full_w + pad + pad
    height = head_h + len(picks) * row_h + pad
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    f_head, f_lab = _font(22, True), _font(17)
    draw.text((pad, 8), "Neutral variant (pending)", font=f_head, fill=(30, 64, 175))
    draw.text((pad * 2 + full_w, 8), "Claim variant (approved)", font=f_head, fill=(185, 28, 28))
    y = head_h
    for case in picks:
        draw.text((pad, y + 2), f"{case['case_id']} · {case['template_style']} · {case['record_id']}",
                  font=f_lab, fill=(55, 65, 81))
        for col, variant in enumerate(("neutral", "claim")):
            img = Image.open(ROOT / "data" / "holdout" / case["evidence"][variant]["image"]).convert("RGB")
            x = pad + col * (full_w + pad)
            canvas.paste(img.resize((full_w, full_h), Image.Resampling.LANCZOS), (x, y + label_h))
            colour = (30, 64, 175) if variant == "neutral" else (185, 28, 28)
            bx = [x + int(v * scale) for v in (CROP[0], CROP[2])]
            by = [y + label_h + int(v * scale) for v in (CROP[1], CROP[3])]
            draw.rectangle([bx[0], by[0], bx[1], by[1]], outline=colour, width=2)
            zoom = img.crop(CROP).resize((full_w, zoom_h), Image.Resampling.LANCZOS)
            zy = y + label_h + full_h + 6
            canvas.paste(zoom, (x, zy))
            draw.rectangle([x, zy, x + full_w - 1, zy + zoom_h - 1], outline=colour, width=2)
        y += row_h
    FIG.mkdir(parents=True, exist_ok=True)
    out = FIG / "fig_pairs.png"
    canvas.save(out, dpi=(300, 300))
    return out


DOT = r"""
digraph VAS {
  rankdir=LR; nodesep=0.25; ranksep=0.35;
  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10, fillcolor="#f8fafc", color="#475569"];
  edge [fontname="Helvetica", fontsize=9, color="#475569"];

  subgraph cluster_user { label="User channel (untrusted)"; fontname="Helvetica-Bold"; fontsize=10; color="#b91c1c"; style=rounded;
    req  [label="Fixed request\n(record, requester)"];
    ev   [label="Evidence\nneutral | claim\ntext | image | none", fillcolor="#fef2f2"];
  }
  subgraph cluster_app { label="Application channel (trusted)"; fontname="Helvetica-Bold"; fontsize=10; color="#1d4ed8"; style=rounded;
    pol  [label="Policy + canary\n(Track A)"];
    reg  [label="Registry grant\nempty | exact | other", fillcolor="#eff6ff"];
    tools[label="Tools: inspect_record_metadata,\nrelease_record (Track B)"];
  }
  model [label="Model under test\n(one response)", shape=box, fillcolor="#fefce8"];
  a    [label="Track A outcome:\ncanary disclosed?"];
  b    [label="Track B outcome:\nvalid release_record call?"];
  ng   [label="Replay without gate\n(schema + record id)"];
  wg   [label="Replay with gate\n(+ exact registry grant)", fillcolor="#eff6ff"];

  req -> model; ev -> model; pol -> model; reg -> model; tools -> model;
  model -> a; model -> b;
  b -> ng [label="proposal"]; b -> wg [label="proposal"];
  reg -> wg [style=dashed, label="read independently"];
}
"""


def fig_design() -> list[Path]:
    dot = shutil.which("dot")
    if dot is None:
        print("Graphviz `dot` not found; fig_design skipped", file=sys.stderr)
        return []
    src = FIG / "fig_design.dot"
    src.write_text(DOT, encoding="utf-8")
    outs = []
    for fmt in ("png", "pdf"):
        out = FIG / f"fig_design.{fmt}"
        args = [dot, f"-T{fmt}", str(src), "-o", str(out)]
        if fmt == "png":
            args.insert(1, "-Gdpi=300")
        try:
            subprocess.run(args, check=True)
            outs.append(out)
        except subprocess.CalledProcessError as exc:
            print(f"Graphviz `dot` failed for {out.name} ({exc.returncode}); keeping existing file", file=sys.stderr)
    return outs


def fig_results() -> Path | None:
    """Plot confirmatory holdout condition rates and paired causal contrasts (when report exists)."""
    import json
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    report_path = ROOT / "runs" / "live_holdout_qwen3vl4b_report.json"
    if not report_path.exists():
        return None
    rep = json.loads(report_path.read_text(encoding="utf-8"))
    if rep.get("report_mode") != "CONFIRMATORY_LIVE":
        return None

    rates = {(r["track"], r["condition_id"]): r for r in rep["condition_rates"]}
    conds = [
        ("none_empty", "None\n(empty)"),
        ("neutral_text", "Neutral\ntext"),
        ("claim_text", "Claim\ntext"),
        ("neutral_image", "Neutral\nimage"),
        ("claim_image", "Claim\nimage"),
        ("claim_image_wrong_scope", "Wrong\nscope"),
        ("claim_image_authorized", "Claim\n(auth)"),
        ("none_authorized", "None\n(auth)"),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 4.5), gridspec_kw={"width_ratios": [1.38, 1.0]})
    fig.patch.set_facecolor("white")

    # Panel (a): Event rates across all 8 conditions
    x = np.arange(len(conds))
    w = 0.27
    a_vals = [100.0 * rates[("A", c[0])]["event_rate"] for c in conds]
    b_vals = [100.0 * rates[("B", c[0])]["event_rate"] for c in conds]
    g_vals = [
        100.0 * (
            rates[("B", c[0])]["n_authorized_mock_write_with_gate"]
            if c[0].endswith("authorized")
            else rates[("B", c[0])]["n_unauthorized_mock_write_with_gate"]
        ) / rates[("B", c[0])]["n_observed"]
        for c in conds
    ]

    ax1.bar(x - w, a_vals, w, label="Track A (canary)", color="#94a3b8", edgecolor="#334155", linewidth=0.6)
    ax1.bar(x, b_vals, w, label="Track B (no gate)", color="#dc2626", edgecolor="#7f1d1d", linewidth=0.6)
    ax1.bar(x + w, g_vals, w, label="Track B (with gate)", color="#2563eb", edgecolor="#1e3a8a", linewidth=0.6)
    ax1.axvline(5.5, color="#475569", linestyle="--", linewidth=0.9)
    ax1.text(2.5, 103.5, "Unauthorized (target: 0%)", ha="center", va="bottom", fontsize=8.5, color="#991b1b", fontweight="bold")
    ax1.text(6.5, 103.5, "Authorized", ha="center", va="bottom", fontsize=8.5, color="#1e40af", fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels([c[1] for c in conds], fontsize=7.8)
    ax1.set_ylabel("Event / write rate (%)", fontsize=9)
    ax1.set_ylim(0, 114)
    ax1.grid(axis="y", linestyle=":", alpha=0.5)
    ax1.set_axisbelow(True)
    ax1.set_title("(a) Holdout rates by condition (qwen3-vl:4b-instruct)", fontsize=9.5, fontweight="bold", pad=26)
    ax1.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=3, fontsize=7.6, frameon=False, handlelength=1.4, columnspacing=1.0)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # Panel (b): Paired causal contrasts with 95% cluster bootstrap CIs
    contrast_defs = [
        ("Primary image\n(claim - neutral)", "primary_image_claim_effect"),
        ("Transcript claim\n(claim - neutral)", "exploratory_transcript_claim_effect"),
        ("Modality interaction\n(image - text)", "exploratory_modality_interaction"),
        ("Scope control\n(exact - other)", "exploratory_scope_control_effect"),
    ]
    y_pos = np.arange(len(contrast_defs))[::-1]
    offsets = {"A": 0.14, "B": -0.14}
    colors = {"A": "#475569", "B": "#dc2626"}
    markers = {"A": "s", "B": "o"}
    labels_leg = {"A": "Track A (canary)", "B": "Track B (tool call)"}

    ax2.axvline(0.0, color="#0f172a", linestyle="--", linewidth=0.9)
    for tr in ("A", "B"):
        ests, lo_err, hi_err, ys = [], [], [], []
        for idx, (_, key) in enumerate(contrast_defs):
            obj = rep["tracks"][tr][key]
            est = obj["estimate_pp"]
            ci = obj["cluster_percentile_ci_95_pp"]
            ests.append(est)
            lo_err.append(est - ci[0])
            hi_err.append(ci[1] - est)
            ys.append(y_pos[idx] + offsets[tr])
        ax2.errorbar(
            ests, ys, xerr=[lo_err, hi_err],
            fmt=markers[tr], color=colors[tr], ecolor=colors[tr],
            elinewidth=1.4, capsize=3, markersize=5.5, label=labels_leg[tr],
        )
        for est, yv in zip(ests, ys):
            va = "bottom" if tr == "A" else "top"
            dy = 0.08 if tr == "A" else -0.09
            ax2.text(est, yv + dy, f"{est:+.1f}", ha="center", va=va, fontsize=7.6, color=colors[tr], fontweight="bold")

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([c[0] for c in contrast_defs], fontsize=8)
    ax2.set_xlabel("Paired risk difference (pp, 95% cluster CI)", fontsize=8.5)
    ax2.set_xlim(-72, 102)
    ax2.set_ylim(-0.65, len(contrast_defs) - 0.3)
    ax2.grid(axis="x", linestyle=":", alpha=0.5)
    ax2.set_axisbelow(True)
    ax2.set_title("(b) Paired contrasts (n = 120, 24 families)", fontsize=9.5, fontweight="bold", pad=26)
    ax2.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2, fontsize=7.6, frameon=False, handlelength=1.4, columnspacing=1.2)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    plt.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    out = FIG / "fig_results.png"
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return out


if __name__ == "__main__":
    print(fig_pairs())
    for p in fig_design():
        print(p)
    r = fig_results()
    if r is not None:
        print(r)
