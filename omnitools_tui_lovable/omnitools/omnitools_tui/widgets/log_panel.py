from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, RichLog, Static

TAGS = {
    "INFO": "bold #00E5FF",
    "OK": "bold #00FF9D",
    "SUCCESS": "bold #00FF9D",
    "WARN": "bold #FFB020",
    "WARNING": "bold #FFB020",
    "ERR": "bold #FF3D71",
    "ERROR": "bold #FF3D71",
    "SYS": "bold #64748B",
}


class LogPanel(Vertical):
    def compose(self) -> ComposeResult:
        with Horizontal(id="log-toolbar"):
            yield Static("▍EXECUTION LOG", classes="section-title", id="log-title")
            yield Button("Clear  [C]", id="clear-btn")
        yield RichLog(id="log", markup=True, wrap=True, highlight=False, auto_scroll=True)

    def write(self, level: str, msg: str) -> None:
        style = TAGS.get(level.upper(), "white")
        ts = datetime.now().strftime("%H:%M:%S")
        self.query_one(RichLog).write(
            f"[#475569]{ts}[/] [{style}]{level:<5}[/] [#CBD5E1]{msg}[/]"
        )

    def clear(self) -> None:
        self.query_one(RichLog).clear()
