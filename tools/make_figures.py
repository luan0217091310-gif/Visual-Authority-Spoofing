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
        subprocess.run(args, check=True)
        outs.append(out)
    return outs


if __name__ == "__main__":
    print(fig_pairs())
    for p in fig_design():
        print(p)
