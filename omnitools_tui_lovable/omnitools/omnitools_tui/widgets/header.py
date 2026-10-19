from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Static

STATES = ("idle", "running", "success", "failed")


class OmniHeader(Horizontal):
    """Brand | centered breadcrumb | status pill."""

    status: reactive[str] = reactive("idle")
    crumb: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Static("◆ OMNI[b]TOOLS[/]", id="brand")
        yield Static("", id="crumb")
        yield Static(" IDLE ", id="status-pill", classes="idle")

    def watch_crumb(self, value: str) -> None:
        self.query_one("#crumb", Static).update(value)

    def watch_status(self, value: str) -> None:
        pill = self.query_one("#status-pill", Static)
        pill.remove_class(*STATES)
        pill.add_class(value)
        pill.update(f" {value.upper()} ")
