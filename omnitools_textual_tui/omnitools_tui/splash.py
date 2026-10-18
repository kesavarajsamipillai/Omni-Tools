"""Short startup splash screen for OmniTools."""
from __future__ import annotations

from pathlib import Path

from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Static


class StartupSplash(ModalScreen[None]):
    """Centered brand screen, dismissed automatically or with a key."""

    CSS_PATH = Path(__file__).with_name("splash.tcss")
    BINDINGS = [
        Binding("escape", "skip", "Skip intro", show=False),
        Binding("enter", "skip", "Skip intro", show=False),
        Binding("space", "skip", "Skip intro", show=False),
    ]

    def __init__(self, brand_name: str, github_id: str):
        super().__init__()
        self.brand_name = brand_name
        self.github_id = github_id

    def compose(self) -> ComposeResult:
        with Vertical(id="splash-card"):
            yield Static("╭─────────╮\n│    ◉    │\n╰─────────╯", id="splash-logo", markup=False)
            yield Static("OMNITOOLS", id="splash-title", markup=False)
            yield Static("OFFLINE UTILITY SUITE", id="splash-subtitle", markup=False)
            yield Static(f"CREATED BY  {self.brand_name}", id="splash-author", markup=False)
            if self.github_id:
                yield Static(self.github_id, id="splash-github", markup=False)
            yield Static("Starting local workspace…", id="splash-message", markup=False)
            yield Static("Press Enter to continue", id="splash-hint", markup=False)

    def on_mount(self) -> None:
        self.set_timer(2.4, self.dismiss)

    def action_skip(self) -> None:
        self.dismiss()
