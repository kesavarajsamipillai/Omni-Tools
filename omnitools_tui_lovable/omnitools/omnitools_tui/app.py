"""OmniTools - Modern Textual Terminal UI.

Offline-first suite with live queue management, ETA countdown, and zero-gap layout.
"""
from __future__ import annotations

import os
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Deque, Dict, Mapping, Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer

from .catalog import CATEGORIES, CATEGORY_BY_ID, TOOLS_BY_CATEGORY, ToolRequest, ToolSpec
from .splash import StartupSplash
from .widgets import LogPanel, OmniHeader, ProgressCard, ToolPanel

Handler = Callable[[ToolRequest, Any], Any]


class ProgressReporter:
    """Thread-safe progress reporter passed to handlers."""
    def __init__(self, on_progress: Callable[[float, str], None]):
        self._on_progress = on_progress

    def report(self, percent: float, message: str = "") -> None:
        self._on_progress(max(0.0, min(100.0, float(percent))), str(message))

    update = report


@dataclass
class Job:
    tool: ToolSpec
    request: ToolRequest
    handler: Handler


class OmniToolsTUI(App[None]):
    TITLE = "OmniTools"
    SUB_TITLE = "100% Offline Suite"
    CSS_PATH = Path(__file__).with_name("theme.tcss")
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("c", "clear_log", "Clear"),
        Binding("tab", "focus_next", "Focus", show=True),
        Binding("f5", "run_tool", "Run", priority=True),
        *[Binding(str(i), f"tab({i - 1})", "Tabs" if i == 1 else "", show=i == 1)
          for i in range(1, 7)],
    ]

    def __init__(
        self,
        handlers: Mapping[str, Handler] | None = None,
        *,
        brand_name: str | None = None,
        github_id: str | None = None,
        show_splash: bool = True,
    ) -> None:
        super().__init__()
        self.handlers: Dict[str, Handler] = dict(handlers or {})
        self.brand_name = (brand_name or os.getenv("OMNITOOLS_AUTHOR") or "Kesavaraj Samipillai").strip()
        self.github_id = (github_id or os.getenv("OMNITOOLS_GITHUB") or "kesavarajsamipillai").strip()
        self.show_splash = show_splash
        self._queue: Deque[Job] = deque()
        self._busy = False

    def compose(self) -> ComposeResult:
        yield OmniHeader(id="header")
        with Horizontal(id="main"):
            yield ToolPanel(id="left")
            with Vertical(id="right"):
                yield LogPanel(id="log-panel")
                yield ProgressCard(id="progress-card")
        yield Footer()

    def on_mount(self) -> None:
        self.log_panel.write("SYS", "OmniTools ready. 100% Offline mode.")
        self.log_panel.write("INFO", "Select a tool, paste paths, and press [b]F5[/] to run.")
        if self.show_splash:
            self.push_screen(StartupSplash(self.brand_name, self.github_id))

    @property
    def log_panel(self) -> LogPanel:
        return self.query_one(LogPanel)

    @property
    def card(self) -> ProgressCard:
        return self.query_one(ProgressCard)

    @property
    def header(self) -> OmniHeader:
        return self.query_one(OmniHeader)

    @property
    def tool_panel(self) -> ToolPanel:
        return self.query_one(ToolPanel)

    # ---- typing protection ------------------------------------------
    def _typing(self) -> bool:
        from textual.widgets import Input, TextArea
        return isinstance(self.focused, (Input, TextArea))

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        if action in ("quit", "clear_log", "tab") and self._typing():
            return False
        return True

    # ---- actions -----------------------------------------------------
    def action_clear_log(self) -> None:
        self.log_panel.clear()

    def action_tab(self, idx: int) -> None:
        self.tool_panel.select_index(idx)

    def action_run_tool(self) -> None:
        panel = self.tool_panel
        tool = panel.tool
        if tool is None:
            self.log_panel.write("WARN", "No tool selected.")
            return

        handler = self.handlers.get(tool.id) or self.handlers.get(tool.category)
        if handler is None:
            self.log_panel.write("WARN", f"No processor registered for {tool.id}.")
            return

        try:
            req = self._validate_and_collect(tool, panel)
        except (ValueError, OSError) as exc:
            self.log_panel.write("WARN", str(exc))
            return

        job = Job(tool=tool, request=req, handler=handler)
        self._queue.append(job)
        if self._busy:
            self.log_panel.write("INFO", f"Queued [b]{tool.name}[/] (Position #{len(self._queue)} in queue)")
        self._sync_queue()

        if not self._busy:
            self._drain_queue()

    def _validate_and_collect(self, tool: ToolSpec, panel: ToolPanel) -> ToolRequest:
        raw_paths = panel.paths()
        paths: list[Path] = []
        for raw in raw_paths:
            p = Path(raw).expanduser()
            if not p.exists():
                raise ValueError(f"Input path does not exist: {p}")
            if tool.input_mode == "folder" and not p.is_dir():
                raise ValueError(f"Expected a folder, got: {p}")
            if tool.input_mode == "files" and not p.is_file():
                raise ValueError(f"Expected a file, got: {p}")
            paths.append(p)

        if tool.needs_input and not paths:
            raise ValueError(f"Add at least one input path before running {tool.name}.")

        output_dir = panel.output_dir()
        if output_dir is not None and output_dir.exists() and not output_dir.is_dir():
            raise ValueError("The specified output path exists but is not a directory.")

        options = panel.option_values()
        return ToolRequest(tool.id, tuple(paths), options, output_dir)

    # ---- events ------------------------------------------------------
    def on_tool_panel_changed(self, msg: ToolPanel.Changed) -> None:
        name = msg.tool.name if msg.tool else "-"
        self.header.crumb = f"[#64748B]{msg.category_label}[/] [#00E5FF]›[/] [b]{name}[/]"

    def on_tool_panel_run_requested(self, _: ToolPanel.RunRequested) -> None:
        self.action_run_tool()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "clear-btn":
            self.action_clear_log()

    # ---- execution queue ---------------------------------------------
    def _sync_queue(self) -> None:
        self.card.set_queue(len(self._queue) - (0 if self._busy else 1) if self._queue else 0)

    @work(exclusive=True, group="runner", thread=True)
    def _drain_queue(self) -> None:
        self._busy = True
        self.call_from_thread(self.tool_panel.set_busy, True)

        while self._queue:
            job = self._queue.popleft()
            self.call_from_thread(self.card.set_queue, len(self._queue))
            self.call_from_thread(setattr, self.header, "status", "running")
            self.call_from_thread(self.card.start, job.tool.name)
            self.call_from_thread(self.log_panel.write, "INFO", f"Started [b]{job.tool.name}[/] on {len(job.request.paths)} item(s)")

            def on_progress(done: float, msg: str) -> None:
                self.call_from_thread(self.card.advance, done, 100)
                if msg:
                    self.call_from_thread(self.log_panel.write, "INFO", msg)

            reporter = ProgressReporter(on_progress)
            ok = True
            try:
                result = job.handler(job.request, reporter)
                ok = True
                detail = str(result) if result is not None else "Completed successfully."
                self.call_from_thread(self.log_panel.write, "OK", detail)
            except Exception as exc:
                ok = False
                self.call_from_thread(self.log_panel.write, "ERR", f"{type(exc).__name__}: {exc}")

            self.call_from_thread(self.card.finish, ok)
            self.call_from_thread(setattr, self.header, "status", "success" if ok else "failed")

        self._busy = False
        self.call_from_thread(self.card.set_queue, 0)
        self.call_from_thread(self.tool_panel.set_busy, False)


def launch(
    handlers: Mapping[str, Handler] | None = None,
    *,
    brand_name: str | None = None,
    github_id: str | None = None,
    show_splash: bool = True,
) -> None:
    OmniToolsTUI(
        handlers=handlers,
        brand_name=brand_name,
        github_id=github_id,
        show_splash=show_splash,
    ).run()
