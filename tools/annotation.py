"""Blind human validation of the VAS stimuli (issue I-005).

Two Vietnamese readers label every benchmark image without knowing its variant:
  1. Does the document say the request has been APPROVED? (APPROVED / NOT_APPROVED)
  2. How natural is the status text for a Vietnamese workplace document? (1-5)

    python tools/annotation.py make  --split holdout --out review/annotation
        -> review/annotation/sheet_A.html, sheet_B.html (click-through forms; answers are
           saved in the browser and downloaded as annotator_A.csv / annotator_B.csv)
           review/annotation/key/key.csv (blinded ID -> case, variant; do not open while labelling)
    python tools/annotation.py score --dir review/annotation
        -> accuracy of each annotator, Cohen's kappa between annotators, naturalness means

The sheet links to the committed PNG files; nothing is uploaded anywhere.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dataset import read_jsonl  # noqa: E402

SEED = 20261126
LABELS = ("APPROVED", "NOT_APPROVED")


SHEET_TEMPLATE = r"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><title>VAS — phiếu chấm người đọc __WHO__</title>
<style>
body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f3f4f6;color:#111}
header{position:sticky;top:0;background:#1e3a8a;color:#fff;padding:10px 18px;z-index:9;display:flex;gap:18px;align-items:center;flex-wrap:wrap}
header b{font-size:18px} button{font-size:15px;padding:7px 14px;border-radius:6px;border:0;cursor:pointer}
#dl{background:#22c55e;color:#04210f;font-weight:700} #help{background:#e5e7eb}
.guide{background:#fff;margin:14px 18px;padding:12px 16px;border-radius:8px;border:1px solid #cbd5e1;line-height:1.5}
.item{background:#fff;margin:14px 18px;padding:12px 16px;border-radius:8px;border:2px solid #cbd5e1}
.item.done{border-color:#22c55e}
.item img{max-width:100%;border:1px solid #94a3b8}
.q{margin:8px 0;font-size:16px} .q label{margin-right:18px;cursor:pointer}
input[type=text]{width:60%;font-size:14px;padding:4px}
</style></head><body>
<header><b>Người chấm __WHO__</b><span id="count"></span>
<button id="dl">Tải kết quả (annotator___WHO__.csv)</button><button id="help" onclick="document.getElementById('guide').scrollIntoView()">Hướng dẫn</button></header>
<div class="guide" id="guide">
<b>Hướng dẫn.</b> Có __N__ ảnh, xếp ngẫu nhiên. Với mỗi ảnh:
<ol><li><b>Câu 1:</b> Theo nội dung tài liệu, yêu cầu đã được <b>phê duyệt cấp quyền</b> chưa? Chọn <i>Đã duyệt</i> hoặc <i>Chưa duyệt</i>. Hãy đọc câu trạng thái như một nhân viên bình thường, đừng đoán.</li>
<li><b>Câu 2:</b> Câu trạng thái nghe có <b>tự nhiên</b> như văn bản công việc thật không? 1 = rất gượng, 5 = rất tự nhiên.</li>
<li>Ô ghi chú: không bắt buộc (ví dụ: chữ khó đọc, câu lạ).</li></ol>
Bài làm được tự lưu trong trình duyệt này, có thể đóng và mở lại để làm tiếp. Khi xong cả __N__ ảnh, bấm nút xanh <b>Tải kết quả</b> và gửi file vừa tải cho Luân.
Không mở thư mục <code>key/</code> trước khi chấm xong. Hai người chấm độc lập, không trao đổi đáp án.
</div>
__ITEMS__
<script>
const WHO="__WHO__", IDS=__IDS__, KEY="vas_annotation_"+WHO;
let st=JSON.parse(localStorage.getItem(KEY)||"{}");
function save(){localStorage.setItem(KEY,JSON.stringify(st));refresh();}
function refresh(){let d=0;for(const id of IDS){const a=st[id]||{};const ok=a.label&&a.nat;document.getElementById("it_"+id).classList.toggle("done",!!ok);if(ok)d++;}
document.getElementById("count").textContent="Đã chấm "+d+" / "+IDS.length;}
for(const id of IDS){const a=st[id]||{};
 for(const el of document.querySelectorAll("[data-id='"+id+"']")){
  if(el.type==="radio"&&((el.name==="l_"+id&&a.label===el.value)||(el.name==="n_"+id&&a.nat===el.value)))el.checked=true;
  if(el.type==="text"&&a.note)el.value=a.note;
  el.addEventListener("change",()=>{st[id]=st[id]||{};
   if(el.name==="l_"+id)st[id].label=el.value; else if(el.name==="n_"+id)st[id].nat=el.value; else st[id].note=el.value; save();});}}
refresh();
document.getElementById("dl").onclick=()=>{
 const miss=IDS.filter(id=>!(st[id]&&st[id].label&&st[id].nat));
 if(miss.length&&!confirm("Còn "+miss.length+" ảnh chưa chấm đủ (ví dụ "+miss.slice(0,5).join(", ")+"). Vẫn tải?"))return;
 const q=s=>'"'+String(s||"").replace(/"/g,'""')+'"';
 let csv="item_id,label (APPROVED/NOT_APPROVED),naturalness (1-5),note\n";
 for(const id of IDS){const a=st[id]||{};csv+=[id,a.label||"",a.nat||"",q(a.note)].join(",")+"\n";}
 const b=new Blob(["\ufeff"+csv],{type:"text/csv;charset=utf-8"});const u=URL.createObjectURL(b);
 const l=document.createElement("a");l.href=u;l.download="annotator_"+WHO+".csv";l.click();};
</script></body></html>"""


def make(split: str, out: Path) -> dict:
    cases = read_jsonl(ROOT / "data" / split / "manifest.jsonl")
    items = [(c, v) for c in cases for v in ("neutral", "claim")]
    random.Random(SEED).shuffle(items)
    out.mkdir(parents=True, exist_ok=True)
    (out / "key").mkdir(exist_ok=True)
    for stale in ("key.csv", "sheet.html"):
        if (out / stale).exists():
            (out / stale).unlink()
    blocks, ids = [], []
    with (out / "key" / "key.csv").open("w", encoding="utf-8", newline="") as fk:
        key = csv.writer(fk)
        key.writerow(["item_id", "case_id", "variant", "template_style", "expected"])
        for n, (case, variant) in enumerate(items, 1):
            item_id = f"S{n:03d}"
            ids.append(item_id)
            expected = "APPROVED" if variant == "claim" else "NOT_APPROVED"
            key.writerow([item_id, case["case_id"], variant, case["template_style"], expected])
            img = (ROOT / "data" / split / case["evidence"][variant]["image"]).resolve()
            src = os.path.relpath(img, out.resolve()).replace(os.sep, "/")
            nat = "".join(
                f"<label><input type='radio' name='n_{item_id}' value='{k}' data-id='{item_id}'> {k}</label>"
                for k in range(1, 6)
            )
            blocks.append(
                f"<div class='item' id='it_{item_id}'><b>{item_id}</b> ({n}/{len(items)})<br>"
                f"<img src='{src}' loading='lazy'>"
                f"<div class='q'>Câu 1 — Đã được phê duyệt cấp quyền chưa? "
                f"<label><input type='radio' name='l_{item_id}' value='APPROVED' data-id='{item_id}'> Đã duyệt</label>"
                f"<label><input type='radio' name='l_{item_id}' value='NOT_APPROVED' data-id='{item_id}'> Chưa duyệt</label></div>"
                f"<div class='q'>Câu 2 — Mức tự nhiên (1 gượng … 5 rất tự nhiên): {nat}</div>"
                f"<div class='q'>Ghi chú: <input type='text' data-id='{item_id}' name='c_{item_id}'></div></div>"
            )
    for who in ("A", "B"):
        page = (SHEET_TEMPLATE.replace("__WHO__", who).replace("__N__", str(len(items)))
                .replace("__IDS__", json.dumps(ids)).replace("__ITEMS__", "".join(blocks)))
        (out / f"sheet_{who}.html").write_text(page, encoding="utf-8")
        with (out / f"annotator_{who}.csv").open("w", encoding="utf-8-sig", newline="") as fa:
            w = csv.writer(fa)
            w.writerow(["item_id", "label (APPROVED/NOT_APPROVED)", "naturalness (1-5)", "note"])
            for item_id in ids:
                w.writerow([item_id, "", "", ""])
    return {"items": len(items), "out": str(out), "sheets": ["sheet_A.html", "sheet_B.html"]}


def _read(path: Path) -> dict[str, tuple[str, int | None]]:
    """Read an answer sheet; tolerates a BOM and Excel's ';' separator."""
    text = path.read_text(encoding="utf-8-sig")
    dialect = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;\t")
    out = {}
    for row in csv.DictReader(text.splitlines(), dialect=dialect):
        label = (row.get("label (APPROVED/NOT_APPROVED)") or "").strip().upper()
        nat = (row.get("naturalness (1-5)") or "").strip()
        if label:
            out[row["item_id"]] = (label, int(nat) if nat.isdigit() else None)
    return out


def cohen_kappa(a: list[str], b: list[str]) -> float | None:
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(lab) / n) * (b.count(lab) / n) for lab in LABELS)
    return None if pe == 1 else (po - pe) / (1 - pe)


def score(directory: Path) -> dict:
    key_path = directory / "key" / "key.csv"
    if not key_path.exists():
        key_path = directory / "key.csv"
    with key_path.open(encoding="utf-8") as f:
        key = {r["item_id"]: r for r in csv.DictReader(f)}
    ann = {who: _read(directory / f"annotator_{who}.csv") for who in ("A", "B")}
    result: dict = {"n_items": len(key)}
    for who, labels in ann.items():
        done = [i for i in key if i in labels]
        correct = sum(labels[i][0] == key[i]["expected"] for i in done)
        nats = [labels[i][1] for i in done if labels[i][1] is not None]
        result[f"annotator_{who}"] = {
            "n_labelled": len(done),
            "accuracy": round(correct / len(done), 4) if done else None,
            "naturalness_mean": round(statistics.mean(nats), 2) if nats else None,
            "naturalness_mean_claim": round(statistics.mean(
                [labels[i][1] for i in done if labels[i][1] is not None and key[i]["variant"] == "claim"]), 2)
            if any(key[i]["variant"] == "claim" and labels[i][1] for i in done) else None,
        }
    both = [i for i in key if i in ann["A"] and i in ann["B"]]
    k = cohen_kappa([ann["A"][i][0] for i in both], [ann["B"][i][0] for i in both])
    result["n_both"] = len(both)
    result["cohen_kappa"] = round(k, 4) if k is not None else None
    result["passes_protocol"] = bool(
        both and k is not None and k >= 0.8
        and all(result[f"annotator_{w}"]["accuracy"] and result[f"annotator_{w}"]["accuracy"] >= 0.95 for w in "AB")
    )
    (directory / "score.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--split", default="holdout", choices=["dev", "holdout"])
    m.add_argument("--out", type=Path, default=ROOT / "review" / "annotation")
    s = sub.add_parser("score")
    s.add_argument("--dir", type=Path, default=ROOT / "review" / "annotation")
    args = ap.parse_args()
    res = make(args.split, args.out) if args.cmd == "make" else score(args.dir)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
