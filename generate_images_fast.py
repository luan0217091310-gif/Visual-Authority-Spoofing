"""High-speed parallel Playwright image renderer for `dataset_1000.json`.

Key optimizations:
1. Uses `playwright.async_api` with a configurable pool of concurrent pages (`--concurrency 8`).
2. Loads each of the 4 HTML templates (`template_gmail.html`, `template_outlook.html`,
   `template_zalo.html`, `template_document.html`) ONCE per worker tab, waiting for fonts/Tailwind
   to settle, and then mutates DOM elements in-place via `page.evaluate(fields)` in ~15ms per image!
3. Supports rendering all 1,000 images (`1280x720`) or a quick sample subset (`--limit N`).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, Page, async_playwright

VIEWPORT_W = 1280
VIEWPORT_H = 720

# Fields that contain rich HTML (paragraphs, lists, tables) vs plain text
HTML_FIELDS = {
    "email-body",
    "outlook-body",
    "zalo-msg-text",
    "doc-content",
}

AVATAR_COLORS = (
    "#0f6cbd",
    "#00897b",
    "#3949ab",
    "#d97706",
    "#7c3aed",
    "#e11d48",
    "#0d9488",
    "#2563eb",
    "#4f46e5",
    "#c026d3",
)


def _find_chrome_executable() -> str | None:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


async def _render_platform_items(
    browser: Browser,
    platform: str,
    template_path: Path,
    items: list[dict[str, Any]],
    out_root: Path,
    concurrency: int,
    scale: int,
) -> int:
    """Render all items for a single platform using a pool of persistent pages pre-loaded with template_path."""
    if not items:
        return 0

    n_workers = min(concurrency, len(items))
    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
    for it in items:
        queue.put_nowait(it)
    for _ in range(n_workers):
        queue.put_nowait(None)

    file_url = template_path.resolve().as_uri()
    completed = 0

    async def _worker(worker_id: int) -> int:
        nonlocal completed
        context = await browser.new_context(
            viewport={"width": VIEWPORT_W, "height": VIEWPORT_H},
            device_scale_factor=scale,
        )
        page: Page = await context.new_page()
        await page.goto(file_url, wait_until="networkidle")
        # Wait briefly for Tailwind CDN and web fonts to initialize once per worker
        await page.wait_for_timeout(350)

        local_count = 0
        while True:
            item = await queue.get()
            if item is None:
                queue.task_done()
                break

            fields = item["fields"]
            color = AVATAR_COLORS[item["index"] % len(AVATAR_COLORS)]

            await page.evaluate(
                """([fields, htmlFields, avatarColor]) => {
                    for (const [id, val] of Object.entries(fields)) {
                        const el = document.getElementById(id);
                        if (!el) continue;
                        if (htmlFields.includes(id)) {
                            el.innerHTML = val;
                        } else {
                            el.textContent = val;
                        }
                    }
                    for (const aid of ['sender-avatar', 'outlook-avatar', 'zalo-avatar', 'zalo-bubble-avatar', 'sidebar-active-avatar']) {
                        const ael = document.getElementById(aid);
                        if (ael) ael.style.backgroundColor = avatarColor;
                    }
                    // Visible provenance label on every image (research ethics: fictional data).
                    if (!document.getElementById('vas-synthetic-label')) {
                        const lab = document.createElement('div');
                        lab.id = 'vas-synthetic-label';
                        lab.textContent = 'SYNTHETIC LAB DATA';
                        lab.style.cssText = 'position:fixed;right:10px;bottom:8px;z-index:2147483647;'
                            + 'font:700 11px Arial,sans-serif;letter-spacing:0.5px;color:#b91c1c;'
                            + 'background:rgba(255,255,255,0.85);border:1px solid #b91c1c;'
                            + 'border-radius:3px;padding:2px 6px;';
                        document.body.appendChild(lab);
                    }
                }""",
                [fields, list(HTML_FIELDS), color],
            )

            out_file = out_root / item["output_image"]
            out_file.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(out_file), type="png", full_page=False)
            local_count += 1
            completed += 1
            queue.task_done()

        await context.close()
        return local_count

    workers = [asyncio.create_task(_worker(w)) for w in range(n_workers)]
    await asyncio.gather(*workers)
    return completed


async def run_batch_render(
    *,
    dataset_path: Path,
    out_root: Path,
    concurrency: int = 6,
    limit: int | None = None,
    scale: int = 1,
) -> dict[str, Any]:
    """Load dataset_1000.json and render screenshots grouped by platform."""
    t0 = time.perf_counter()
    rows: list[dict[str, Any]] = json.loads(dataset_path.read_text(encoding="utf-8"))

    by_platform: dict[str, list[dict[str, Any]]] = {"gmail": [], "outlook": [], "zalo": [], "document": []}
    for r in rows:
        by_platform.setdefault(r["platform"], []).append(r)

    if limit is not None:
        # Take balanced slice across platforms
        per_plat = max(1, limit // 4)
        for p in by_platform:
            by_platform[p] = by_platform[p][:per_plat]

    exe = _find_chrome_executable()
    launch_kwargs: dict[str, Any] = {"headless": True}
    if exe:
        launch_kwargs["executable_path"] = exe

    total_rendered = 0
    per_platform_counts: dict[str, int] = {}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(**launch_kwargs)
        try:
            for platform, p_items in by_platform.items():
                if not p_items:
                    continue
                tpl_path = dataset_path.parent / f"template_{platform}.html"
                cnt = await _render_platform_items(
                    browser=browser,
                    platform=platform,
                    template_path=tpl_path,
                    items=p_items,
                    out_root=out_root,
                    concurrency=concurrency,
                    scale=scale,
                )
                per_platform_counts[platform] = cnt
                total_rendered += cnt
                print(f"[{platform}] Rendered {cnt} images.")
        finally:
            await browser.close()

    elapsed = round(time.perf_counter() - t0, 2)
    return {
        "total_rendered": total_rendered,
        "per_platform": per_platform_counts,
        "elapsed_seconds": elapsed,
        "images_per_second": round(total_rendered / max(elapsed, 0.01), 2),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fast parallel Playwright renderer for dataset_1000.json.")
    parser.add_argument("--dataset", type=Path, default=Path("dataset_1000.json"))
    parser.add_argument("--out-root", type=Path, default=Path("."))
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--limit", type=int, default=None, help="Optional total image limit for quick preview.")
    parser.add_argument("--scale", type=int, default=1, help="Device scale factor (1 for 1280x720, 2 for 2560x1440).")
    args = parser.parse_args(argv)

    summary = asyncio.run(
        run_batch_render(
            dataset_path=args.dataset,
            out_root=args.out_root,
            concurrency=args.concurrency,
            limit=args.limit,
            scale=args.scale,
        )
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
