"""Tool registry. Replace demo jobs with real implementations."""
from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, List, Literal, Union

OptionKind = Literal["switch", "input"]


@dataclass
class Option:
    key: str
    label: str
    kind: OptionKind = "switch"
    default: Union[bool, str] = False
    placeholder: str = ""


@dataclass
class RunContext:
    tool_name: str
    paths: List[str]
    options: Dict[str, Union[bool, str]]
    log: Callable[[str, str], None]
    progress: Callable[[int, int], None]


@dataclass
class Tool:
    id: str
    name: str
    run: Callable[[RunContext], Awaitable[None]]
    options: List[Option] = field(default_factory=list)


async def demo_job(ctx: RunContext) -> None:
    """Simulated job - swap for real work (use asyncio.to_thread for blocking IO)."""
    targets = ctx.paths or ["<no input>"]
    steps = max(len(targets) * 8, 12)
    ctx.log("INFO", f"Starting [b]{ctx.tool_name}[/] on {len(targets)} item(s)")
    for i in range(1, steps + 1):
        await asyncio.sleep(random.uniform(0.05, 0.2))
        if i % 8 == 0:
            ctx.log("OK", f"Processed {targets[(i // 8 - 1) % len(targets)]}")
        elif random.random() < 0.06:
            ctx.log("WARN", f"Step {i}: slow read, retrying")
        ctx.progress(i, steps)
    ctx.log("OK", "Completed successfully")


def _t(id_: str, name: str, *opts: Option) -> Tool:
    return Tool(id_, name, demo_job, list(opts))


CATEGORIES: Dict[str, List[Tool]] = {
    "PDF": [
        _t("pdf.merge", "Merge PDFs", Option("sort", "Sort by name", default=True),
           Option("out", "Output file", "input", "merged.pdf")),
        _t("pdf.split", "Split PDF", Option("range", "Page ranges", "input", "", "1-3,5")),
        _t("pdf.compress", "Compress PDF", Option("aggressive", "Aggressive mode")),
    ],
    "DOCS": [
        _t("docs.md2pdf", "Markdown -> PDF", Option("toc", "Table of contents", default=True)),
        _t("docs.docx2txt", "DOCX -> Text"),
    ],
    "IMAGES": [
        _t("img.resize", "Batch Resize", Option("width", "Width (px)", "input", "1920"),
           Option("keep", "Keep aspect", default=True)),
        _t("img.webp", "Convert to WebP", Option("quality", "Quality", "input", "82")),
        _t("img.strip", "Strip EXIF"),
    ],
    "MEDIA": [
        _t("media.mp3", "Extract Audio", Option("bitrate", "Bitrate", "input", "192k")),
        _t("media.trim", "Trim Video", Option("start", "Start", "input", "00:00:00")),
    ],
    "SORTER": [
        _t("sort.ext", "Sort by Extension", Option("dry", "Dry run", default=True)),
        _t("sort.date", "Sort by Date", Option("dry", "Dry run", default=True)),
    ],
    "UTILS": [
        _t("util.hash", "Checksum (SHA-256)"),
        _t("util.dupes", "Find Duplicates", Option("delete", "Delete duplicates")),
    ],
}
