from __future__ import annotations

import time

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import ProgressBar, Static


class ProgressCard(Vertical):
    """Active task, dynamic ETA, queue badge, full-width bar."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self._start = 0.0
        self._task_name: Static | None = None
        self._eta: Static | None = None
        self._queue_badge: Static | None = None
        self._bar: ProgressBar | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="progress-meta"):
            yield Static("No active task", id="task-name")
            yield Static("ETA --:--", id="eta")
            yield Static(" Queued: 0 ", id="queue-badge")
        yield ProgressBar(total=100, show_eta=False, id="bar")

    def on_mount(self) -> None:
        try:
            self._task_name = self.query_one("#task-name", Static)
            self._eta = self.query_one("#eta", Static)
            self._queue_badge = self.query_one("#queue-badge", Static)
            self._bar = self.query_one(ProgressBar)
        except Exception:
            pass

    def _get_task_name(self) -> Static:
        if self._task_name is None:
            self._task_name = self.query_one("#task-name", Static)
        return self._task_name

    def _get_eta(self) -> Static:
        if self._eta is None:
            self._eta = self.query_one("#eta", Static)
        return self._eta

    def _get_queue_badge(self) -> Static:
        if self._queue_badge is None:
            self._queue_badge = self.query_one("#queue-badge", Static)
        return self._queue_badge

    def _get_bar(self) -> ProgressBar:
        if self._bar is None:
            self._bar = self.query_one(ProgressBar)
        return self._bar

    def start(self, name: str) -> None:
        self._start = time.monotonic()
        try:
            self._get_task_name().update(f">> [b]{name}[/]")
            self._get_eta().update("ETA --:--")
            self._get_bar().update(total=100, progress=0)
            self.add_class("active")
        except Exception:
            pass

    def advance(self, done: int | float, total: int | float = 100) -> None:
        try:
            bar = self._get_bar()
            bar.update(total=total, progress=done)
            elapsed = time.monotonic() - self._start
            if done > 1:
                remaining = max(0.0, elapsed / done * (total - done))
                m, s = divmod(int(remaining + 0.5), 60)
                self._get_eta().update(f"ETA {m:02d}:{s:02d}")
        except Exception:
            pass

    def finish(self, ok: bool) -> None:
        try:
            self.remove_class("active")
            self._get_eta().update("ETA 00:00" if ok else "ETA --:--")
            self._get_task_name().update(
                "[#00FF9D][OK] Done[/]" if ok else "[#FF3D71][FAIL] Failed[/]"
            )
        except Exception:
            pass

    def set_queue(self, n: int) -> None:
        try:
            badge = self._get_queue_badge()
            badge.update(f" Queued: {n} ")
            badge.set_class(n > 0, "has-items")
        except Exception:
            pass
