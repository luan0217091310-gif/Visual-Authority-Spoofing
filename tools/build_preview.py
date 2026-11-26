"""Build a PDF preview of paper/main.tex without a TeX installation.

This converts the LaTeX subset used by main.tex to HTML (LNCS-like layout: A4 page,
122 mm x 193 mm text block, Times, numbered sections/tables/figures/equations, numbered
citations) and prints it to PDF with headless Chromium via Playwright.

It is a reading preview, not the submission build: line breaks and page breaks differ
from llncs.cls. For the official PDF, compile main.tex with pdfLaTeX (MiKTeX, TeX Live
or Overleaf). Unsupported commands raise an error instead of being dropped silently.

Usage: python tools/build_preview.py   ->  paper/build/main_preview.pdf (+ .html)
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
BUILD = PAPER / "build"

ACCENTS = {("'", "c"): "ć", ("`", "e"): "è", ("'", "e"): "é", ("'", "a"): "á", ('"', "o"): "ö", ('"', "u"): "ü"}
SIMPLE = {
    r"\%": "%", r"\&": "&amp;", r"\_": "_", r"\#": "#", r"\$": "$",
    r"\noindent": "", r"\centering": "", r"\vs.": "vs.", r"\ ": " ", r"\\": "<br>",
}
MATH_SYMBOLS = {
    r"\Delta": "Δ", r"\kappa": "κ", r"\times": "×", r"\ge": "≥", r"\le": "≤", r"\alpha": "α", r"\cdot": "·", r"\%": "%",
}


def find_group(s: str, i: int, open_ch: str = "{", close_ch: str = "}") -> tuple[str, int]:
    """Return (content, index after closing brace) for a group starting at s[i] == open_ch."""
    assert s[i] == open_ch, (s[i:i + 30], i)
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "\\":
            continue
        if s[j] == open_ch and (j == 0 or s[j - 1] != "\\"):
            depth += 1
        elif s[j] == close_ch and s[j - 1] != "\\":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    raise ValueError(f"unbalanced group at {s[i:i + 40]!r}")


def load_macros() -> dict[str, str]:
    macros: dict[str, str] = {}
    text = (PAPER / "generated" / "numbers.tex").read_text(encoding="utf-8")
    text += (PAPER / "main.tex").read_text(encoding="utf-8").split(r"\begin{document}")[0]
    for m in re.finditer(r"\\newcommand\{\\(\w+)\}", text):
        body, _ = find_group(text, m.end())
        macros[m.group(1)] = body
    return macros


def expand_macros(s: str, macros: dict[str, str]) -> str:
    for _ in range(5):
        new = re.sub(r"\\(vas\w+|pending)(\{\})?", lambda m: macros[m.group(1)], s)
        if new == s:
            break
        s = new
    return s


def math_to_html(m: str) -> str:
    out = html.escape(m, quote=False)
    while r"\frac" in out:
        i = out.index(r"\frac")
        num, j = find_group(out, i + 5)
        den, k = find_group(out, j)
        out = out[:i] + f"({num})/({den})" + out[k:]
    while r"\text{" in out:
        i = out.index(r"\text{")
        body, j = find_group(out, i + 5)
        out = out[:i] + f"\x00{body}\x01" + out[j:]
    for k, v in MATH_SYMBOLS.items():
        out = out.replace(k, v)
    out = re.sub(r"_\{([^{}]*)\}", r"<sub>\1</sub>", out)
    out = re.sub(r"\^\{([^{}]*)\}", r"<sup>\1</sup>", out)
    out = re.sub(r"_([A-Za-z0-9+\-])", r"<sub>\1</sub>", out)
    out = re.sub(r"\^([A-Za-z0-9+\-])", r"<sup>\1</sup>", out)
    out = out.replace("\x00", '<span class="mtext">').replace("\x01", "</span>")
    if "\\" in re.sub(r"<[^>]+>", "", out):
        raise ValueError(f"unsupported math: {m!r}")
    return f'<span class="math">{out}</span>'


class Converter:
    def __init__(self, src: str, macros: dict[str, str]):
        self.src = src
        self.macros = macros
        self.labels: dict[str, str] = {}
        self.cites: dict[str, int] = {}
        self._prescan()

    def _prescan(self) -> None:
        sec = tab = fig = eq = 0
        token = re.compile(r"\\(section|begin\{table\}|begin\{figure\}|begin\{equation\}|label|bibitem)\{?([^}]*)\}?")
        current = None
        n_bib = 0
        for m in token.finditer(self.src):
            kind = m.group(1)
            if kind == "section":
                sec += 1
                current = str(sec)
            elif kind.startswith("begin{table"):
                tab += 1
                current = str(tab)
            elif kind.startswith("begin{figure"):
                fig += 1
                current = str(fig)
            elif kind.startswith("begin{equation"):
                eq += 1
                current = str(eq)
            elif kind == "label":
                self.labels[m.group(2)] = current or "?"
            elif kind == "bibitem":
                n_bib += 1
                self.cites[m.group(2)] = n_bib

    # ---------------------------------------------------------------- inline
    def inline(self, s: str) -> str:
        s = expand_macros(s, self.macros)
        out: list[str] = []
        i = 0
        while i < len(s):
            ch = s[i]
            if ch == "$":
                j = s.index("$", i + 1)
                out.append(math_to_html(s[i + 1:j]))
                i = j + 1
            elif ch == "\\":
                i = self._command(s, i, out)
            elif ch == "~":
                out.append("&nbsp;")
                i += 1
            elif s.startswith("---", i):
                out.append("—")
                i += 3
            elif s.startswith("--", i):
                out.append("–")
                i += 2
            elif s.startswith("``", i):
                out.append("“")
                i += 2
            elif s.startswith("''", i):
                out.append("”")
                i += 2
            elif ch in "{}":
                i += 1
            elif ch == "%":
                j = s.find("\n", i)
                i = len(s) if j < 0 else j
            else:
                out.append(html.escape(ch, quote=False))
                i += 1
        return "".join(out)

    def _command(self, s: str, i: int, out: list[str]) -> int:
        for k, v in SIMPLE.items():
            if s.startswith(k, i) and not (k[-1].isalpha() and i + len(k) < len(s) and s[i + len(k)].isalpha()):
                out.append(v)
                return i + len(k)
        if s[i + 1] in "'`\"":
            m = re.match(r"\\(['`\"])\{?(\w)\}?", s[i:])
            out.append(ACCENTS[(m.group(1), m.group(2))])
            return i + m.end()
        m = re.match(r"\\([A-Za-z]+)", s[i:])
        name = m.group(1)
        j = i + m.end()
        wrappers = {"textbf": "b", "emph": "em", "texttt": "code", "textit": "i"}
        if name in wrappers:
            body, k = find_group(s, j)
            out.append(f"<{wrappers[name]}>{self.inline(body)}</{wrappers[name]}>")
            return k
        if name == "textcolor":
            colour, k = find_group(s, j)
            body, k = find_group(s, k)
            out.append(f'<span style="color:{colour}">{self.inline(body)}</span>')
            return k
        if name == "url":
            body, k = find_group(s, j)
            out.append(f'<a href="{body}">{html.escape(body)}</a>')
            return k
        if name == "doi":
            body, k = find_group(s, j)
            out.append(f'<a href="https://doi.org/{body}">https://doi.org/{html.escape(body)}</a>')
            return k
        if name == "cite":
            body, k = find_group(s, j)
            nums = sorted(self.cites[key.strip()] for key in body.split(","))
            out.append("[" + ", ".join(str(n) for n in nums) + "]")
            return k
        if name == "ref":
            body, k = find_group(s, j)
            out.append(self.labels[body])
            return k
        if name == "label":
            _, k = find_group(s, j)
            return k
        if name == "discintname":
            out.append("Disclosure of Interests.")
            return j
        raise ValueError(f"unsupported command \\{name} near {s[i:i + 50]!r}")

    # ----------------------------------------------------------------- blocks
    def tabular(self, body: str) -> str:
        body = body.replace(r"\centering", "").strip()
        if body.startswith(r"\input"):
            name, _ = find_group(body, len(r"\input"))
            body = (PAPER / f"{name}.tex").read_text(encoding="utf-8")
        spec_start = body.index(r"\begin{tabular}") + len(r"\begin{tabular}")
        spec, k = find_group(body, spec_start)
        inner = body[k:body.index(r"\end{tabular}")]
        aligns = [c for c in re.sub(r"p\{[^}]*\}", "l", spec) if c in "lcr"]
        rows_html = []
        rule_next = ""
        header_done = False
        for raw in re.split(r"\\\\", inner):
            line = raw.strip()
            rules = re.findall(r"\\(toprule|midrule|bottomrule)", line)
            line = re.sub(r"\\(toprule|midrule|bottomrule)", "", line).strip()
            if "midrule" in rules:
                rule_next = "mid"
                header_done = True
            if not line:
                continue
            cells = [c.strip() for c in line.split("&")]
            tag = "td" if header_done or rows_html else "th"
            tds = "".join(
                f'<{tag} class="a-{aligns[n] if n < len(aligns) else "l"}">{self.inline(c)}</{tag}>'
                for n, c in enumerate(cells)
            )
            cls = ' class="rule"' if rule_next == "mid" else ""
            rule_next = ""
            rows_html.append(f"<tr{cls}>{tds}</tr>")
        return f'<table class="booktabs">{"".join(rows_html)}</table>'

    def float_env(self, kind: str, body: str) -> str:
        cap, label = "", ""
        if r"\caption" in body:
            i = body.index(r"\caption")
            cap, j = find_group(body, i + len(r"\caption"))
            body = body[:i] + body[j:]
        m = re.search(r"\\label\{([^}]*)\}", body)
        if m:
            label = m.group(1)
            body = body.replace(m.group(0), "")
        num = self.labels.get(label, "?")
        name = "Table" if kind == "table" else "Fig."
        caption = f'<div class="caption"><b>{name} {num}.</b> {self.inline(cap)}</div>'
        if kind == "table":
            return f'<div class="float">{caption}{self.tabular(body)}</div>'
        m = re.search(r"\\includegraphics(\[[^\]]*\])?\{([^}]*)\}", body)
        src = (PAPER / m.group(2)).resolve().as_uri()
        return f'<div class="float"><img src="{src}">{caption}</div>'

    def list_env(self, tag: str, body: str) -> str:
        items = [x.strip() for x in re.split(r"\\item\s", body) if x.strip()]
        return f"<{tag}>" + "".join(f"<li>{self.inline(x)}</li>" for x in items) + f"</{tag}>"

    def body(self, s: str) -> str:
        out: list[str] = []
        sec_n = 0
        pos = 0
        env_re = re.compile(
            r"\\begin\{(table|figure|enumerate|itemize|equation|abstract|credits|thebibliography)\}"
            r"|\\section\{|\\subsubsection\{|\\paragraph\{|\\maketitle|\\keywords\{|\n\s*\n"
        )
        para: list[str] = []

        def flush() -> None:
            text = "".join(para).strip()
            para.clear()
            if text:
                out.append(f"<p>{self.inline(text)}</p>")

        while True:
            m = env_re.search(s, pos)
            if not m:
                para.append(s[pos:])
                flush()
                break
            para.append(s[pos:m.start()])
            tok = m.group(0)
            if tok.strip() == "":
                flush()
                pos = m.end()
                continue
            if tok.startswith(r"\begin"):
                flush()
                env = m.group(1)
                end_tag = rf"\end{{{env}}}"
                k = s.index(end_tag, m.end())
                inner = s[m.end():k]
                pos = k + len(end_tag)
                if env in ("table", "figure"):
                    out.append(self.float_env(env, re.sub(r"^\[[^\]]*\]", "", inner.strip())))
                elif env in ("enumerate", "itemize"):
                    out.append(self.list_env("ol" if env == "enumerate" else "ul", inner))
                elif env == "equation":
                    lm = re.search(r"\\label\{([^}]*)\}", inner)
                    num = self.labels.get(lm.group(1), "") if lm else ""
                    inner = re.sub(r"\\label\{[^}]*\}", "", inner).strip().rstrip(",")
                    out.append(f'<div class="eq">{math_to_html(expand_macros(inner, self.macros))},'
                               f'<span class="eqn">({num or 1})</span></div>')
                elif env == "abstract":
                    kw = ""
                    if r"\keywords" in inner:
                        i = inner.index(r"\keywords")
                        kwb, j = find_group(inner, i + len(r"\keywords"))
                        kw = "<p class='kw'><b>Keywords:</b> " + self.inline(kwb.replace(r"\and", "·")) + "</p>"
                        inner = inner[:i] + inner[j:]
                    out.append(f'<div class="abstract"><p><b>Abstract.</b> {self.inline(inner.strip())}</p>{kw}</div>')
                elif env == "credits":
                    out.append(f'<div class="credits">{self.body(inner)}</div>')
                elif env == "thebibliography":
                    inner = re.sub(r"^\{\d+\}", "", inner.strip())
                    items = re.split(r"\\bibitem\{[^}]*\}", inner)[1:]
                    lis = "".join(f"<li>{self.inline(x.strip())}</li>" for x in items)
                    out.append(f'<h2 class="refs">References</h2><ol class="bib">{lis}</ol>')
                continue
            if tok == r"\maketitle":
                flush()
                pos = m.end()
                continue
            arg, end = find_group(s, m.end() - 1)
            pos = end
            if tok == r"\section{":
                flush()
                sec_n += 1
                out.append(f"<h2>{sec_n}&nbsp;&nbsp;{self.inline(arg)}</h2>")
                lm = re.match(r"\s*\\label\{[^}]*\}", s[pos:])
                if lm:
                    pos += lm.end()
            elif tok == r"\subsubsection{":
                flush()
                para.append(f"\\textbf{{{arg}}} ")
            elif tok == r"\paragraph{":
                flush()
                para.append(f"\\textbf{{{arg}}} ")
        return "".join(out)


def front_matter(doc: str, conv: Converter) -> str:
    def grab(cmd: str) -> str:
        i = doc.index(cmd)
        body, _ = find_group(doc, i + len(cmd))
        return body

    title = conv.inline(grab(r"\title"))
    authors = grab(r"\author")
    authors = re.sub(r"\\orcidID\{[^}]*\}", "", authors)
    authors = re.sub(r"\\inst\{(\d+)\}", r"$^{\1}$", authors)
    authors_html = conv.inline(authors.replace(r"\and", ", "))
    inst = grab(r"\institute")
    inst = re.sub(r"\\email\{([^}]*)\}", r"\\texttt{\1}", inst)
    inst_html = conv.inline(inst)
    return (f'<h1>{title}</h1><div class="authors">{authors_html}</div>'
            f'<div class="inst"><sup>1</sup> {inst_html}</div>')


CSS = """
@page { size: A4; margin: 52mm 44mm 52mm 44mm; }
body { font-family: 'Times New Roman', Times, serif; font-size: 10pt; line-height: 1.22; color:#000; }
h1 { font-size: 14pt; text-align: center; margin: 0 0 12pt 0; line-height: 1.25; }
.authors { text-align: center; font-size: 10pt; margin-bottom: 6pt; }
.inst { text-align: center; font-size: 9pt; margin-bottom: 14pt; }
.abstract { font-size: 9pt; margin: 0 6mm 12pt 6mm; text-align: justify; }
.abstract p { text-indent: 0; margin: 0 0 4pt 0; }
h2 { font-size: 12pt; margin: 16pt 0 8pt 0; }
h2.refs { font-size: 12pt; }
p { margin: 0; text-align: justify; text-indent: 1.5em; hyphens: auto; }
h2 + p, .float + p { text-indent: 0; }
ol, ul { margin: 4pt 0 4pt 0; padding-left: 1.6em; }
li { text-align: justify; margin-bottom: 2pt; }
.float { margin: 10pt 0; break-inside: avoid; text-align: center; }
.float img { width: 100%; }
.caption { font-size: 9pt; text-align: justify; margin: 4pt 0; }
table.booktabs { border-collapse: collapse; margin: 0 auto; font-size: 9pt; border-top: 1.2pt solid #000; border-bottom: 1.2pt solid #000; }
table.booktabs th { border-bottom: 0.6pt solid #000; padding: 2pt 5pt; font-weight: normal; }
table.booktabs td { padding: 1.5pt 5pt; vertical-align: top; }
tr.rule td { border-top: 0.6pt solid #000; }
.a-l { text-align: left; } .a-c { text-align: center; } .a-r { text-align: right; }
code { font-family: 'Courier New', monospace; font-size: 9pt; }
.math { font-style: italic; } .math .mtext { font-style: normal; }
.eq { text-align: center; margin: 6pt 0; position: relative; }
.eqn { position: absolute; right: 0; font-style: normal; }
.credits { font-size: 9pt; margin-top: 12pt; }
.credits p { text-indent: 0; margin-bottom: 4pt; }
ol.bib { font-size: 9pt; padding-left: 2.2em; }
ol.bib li { margin-bottom: 2pt; }
a { color: #1d4ed8; text-decoration: none; word-break: break-all; }
"""


def main() -> int:
    src = (PAPER / "main.tex").read_text(encoding="utf-8")
    doc = src.split(r"\begin{document}", 1)[1].split(r"\end{document}", 1)[0]
    conv = Converter(doc, load_macros())
    head = front_matter(doc, conv)
    body_src = doc[doc.index(r"\maketitle"):]
    html_doc = (f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head>"
                f"<body>{head}{conv.body(body_src)}</body></html>")
    BUILD.mkdir(parents=True, exist_ok=True)
    out_html = BUILD / "main_preview.html"
    out_html.write_text(html_doc, encoding="utf-8")

    from playwright.sync_api import sync_playwright

    sys.path.insert(0, str(ROOT))
    from dataset import _PlaywrightRenderer

    exe = _PlaywrightRenderer()._find_chrome_executable()
    footer = ("<div style='font-size:7pt;width:100%;text-align:center;font-family:Times New Roman;color:#555'>"
              "<span class='pageNumber'></span> &nbsp;·&nbsp; preview build (HTML); compile main.tex with llncs "
              "for the official layout</div>")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, **({"executable_path": exe} if exe else {}))
        page = browser.new_page()
        page.goto(out_html.as_uri(), wait_until="load")
        page.pdf(path=str(BUILD / "main_preview.pdf"), format="A4", display_header_footer=True,
                 header_template="<div></div>", footer_template=footer,
                 margin={"top": "52mm", "bottom": "52mm", "left": "44mm", "right": "44mm"})
        browser.close()
    print(BUILD / "main_preview.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
