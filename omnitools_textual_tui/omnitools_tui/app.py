"""Keyboard-first Textual front end for OmniTools.

Processing handlers are supplied by the host application. Synchronous local
handlers run in a Textual worker thread and may report progress safely.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Button, Input, ProgressBar, RichLog, Select, Static, Switch, Tab, Tabs, TextArea

from .catalog import CATEGORIES, CATEGORY_BY_ID, TOOLS_BY_CATEGORY, FieldSpec, ToolRequest, ToolSpec

Handler = Callable[[ToolRequest, "ProgressReporter"], Any]


class ProgressReporter:
    """Progress API passed to backend handlers. Safe to call from a worker."""
    def __init__(self, callback: Callable[[float, str], None]):
        self._callback = callback

    def report(self, percent: float, message: str = "") -> None:
        self._callback(max(0.0, min(100.0, float(percent))), str(message))

    update = report


class OmniToolsTUI(App[None]):
    """Full-screen offline utility TUI; processor functions are injected."""
    TITLE = "OmniTools"
    SUB_TITLE = "Offline Utility Suite"
    CSS_PATH = Path(__file__).with_name("styles.tcss")
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("c", "clear_console", "Clear console"),
        Binding("f5", "run_tool", "Run tool", priority=True),
        Binding("1", "switch_category('pdf')", "PDF", show=False),
        Binding("2", "switch_category('documents')", "Documents", show=False),
        Binding("3", "switch_category('images')", "Images", show=False),
        Binding("4", "switch_category('media')", "Audio & media", show=False),
        Binding("5", "switch_category('sorter')", "Folder sorter", show=False),
        Binding("6", "switch_category('utilities')", "Utilities", show=False),
    ]

    active_category = reactive("pdf")
    active_tool = reactive("pdf.unlock")
    job_status = reactive("IDLE")
    progress_value = reactive(0.0)

    def __init__(self, handlers: Mapping[str, Handler] | None = None):
        super().__init__()
        self.handlers = dict(handlers or {})
        self._last_progress_note = "Ready. Choose a tool and add input paths."

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static("OMNITOOLS  /  LOCAL FILE WORKSPACE", id="app-title"),
            Static("PDF Tools  ·  Offline", id="mode-label"),
            Static("●  IDLE", id="status-pill", classes="status-idle", markup=False),
            id="header",
        )
        with Horizontal(id="main-split"):
            with Vertical(id="left-panel"):
                yield Static("TOOL CONFIGURATION", classes="panel-heading")
                yield Tabs(*(Tab(category.short_label, id=category.key) for category in CATEGORIES), active="pdf", id="category-tabs")
                with VerticalScroll(id="form-scroll"):
                    yield Static("Selected tool", classes="field-label")
                    yield Select([(tool.name, tool.id) for tool in TOOLS_BY_CATEGORY["pdf"]], value="pdf.unlock", id="tool-select", allow_blank=False)
                    yield Static("Input paths  ·  one path per line", classes="field-label")
                    yield TextArea(placeholder="Paste local file paths here. For a folder tool, enter one folder path.", id="input-paths", soft_wrap=True)
                    yield Static("Options", classes="field-label")
                    yield Vertical(id="options-fields")
                    yield Static("Output folder  ·  leave empty for handler default", classes="field-label")
                    yield Input(placeholder="/path/to/output", id="output-dir")
                    yield Button("Run selected tool   F5", id="run-tool", classes="primary", variant="primary")
            with Vertical(id="right-panel"):
                with Horizontal(id="console-toolbar"):
                    yield Static("LIVE EXECUTION LOG", id="console-title")
                    yield Button("Clear  C", id="clear-console")
                yield RichLog(id="console", wrap=True, markup=False, auto_scroll=True, min_width=40)
                yield ProgressBar(total=100, show_eta=False, id="progress")
                yield Static("Ready. Choose a tool and add input paths.", id="progress-note")
        yield Static("Q  Quit     C  Clear console     Tab  Focus next     1–6  Switch category     F5  Run selected tool", id="footer")

    async def on_mount(self) -> None:
        await self._render_fields()
        self._log("INFO", "OmniTools TUI ready. All processing stays on your machine.")

    async def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        category_key = event.tab.id
        if not category_key or category_key not in CATEGORY_BY_ID:
            return
        self.active_category = category_key
        choices = TOOLS_BY_CATEGORY[category_key]
        selector = self.query_one("#tool-select", Select)
        selector.set_options([(tool.name, tool.id) for tool in choices])
        self.active_tool = choices[0].id
        selector.value = self.active_tool
        await self._render_fields()
        self._update_mode_label()

    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "tool-select" or not event.value:
            return
        self.active_tool = str(event.value)
        await self._render_fields()
        self._update_mode_label()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-tool":
            self.action_run_tool()
        elif event.button.id == "clear-console":
            self.action_clear_console()

    async def _render_fields(self) -> None:
        container = self.query_one("#options-fields", Vertical)
        await container.remove_children()
        tool = self._selected_tool()
        if tool is None or not tool.fields:
            await container.mount(Static("No extra options for this tool.", classes="field-label"))
            return
        widgets = [self._field_widget(field) for field in tool.fields]
        await container.mount(*widgets)

    @staticmethod
    def _field_widget(field: FieldSpec) -> Any:
        control_id = f"option-{field.key}"
        if field.kind == "toggle":
            return Horizontal(Static(field.label), Switch(value=bool(field.default), id=control_id), classes="field-row")
        if field.kind == "choice":
            return Vertical(
                Static(field.label, classes="field-label"),
                Select([(choice, choice) for choice in field.choices], value=str(field.default), allow_blank=False, id=control_id),
            )
        return Vertical(
            Static(field.label, classes="field-label"),
            Input(value=str(field.default), placeholder=field.placeholder, password=field.kind == "password", id=control_id),
        )

    def _selected_tool(self) -> ToolSpec | None:
        from .catalog import TOOL_BY_ID
        return TOOL_BY_ID.get(self.active_tool)

    def _collect_request(self, tool: ToolSpec) -> ToolRequest:
        raw_paths = self.query_one("#input-paths", TextArea).text.splitlines()
        paths: list[Path] = []
        for raw in raw_paths:
            value = raw.strip().strip('"').strip("'")
            if not value:
                continue
            path = Path(value).expanduser()
            if not path.exists():
                raise ValueError(f"Input path does not exist: {path}")
            if tool.input_mode == "folder" and not path.is_dir():
                raise ValueError(f"Expected a folder, got: {path}")
            if tool.input_mode == "files" and not path.is_file():
                raise ValueError(f"Expected a file, got: {path}")
            paths.append(path)
        if tool.needs_input and not paths:
            raise ValueError("Add at least one input path before running this tool.")
        output_value = self.query_one("#output-dir", Input).value.strip()
        output_dir = Path(output_value).expanduser() if output_value else None
        if output_dir is not None and output_dir.exists() and not output_dir.is_dir():
            raise ValueError("The output path exists but is not a directory.")
        options: dict[str, Any] = {}
        for field in tool.fields:
            control_id = f"#option-{field.key}"
            if field.kind == "toggle":
                options[field.key] = self.query_one(control_id, Switch).value
            elif field.kind == "choice":
                options[field.key] = self.query_one(control_id, Select).value
            else:
                options[field.key] = self.query_one(control_id, Input).value
        return ToolRequest(tool.id, tuple(paths), options, output_dir)

    def action_run_tool(self) -> None:
        if self.job_status == "RUNNING":
            self._log("WARNING", "A task is already running.")
            return
        tool = self._selected_tool()
        if tool is None:
            self._log("ERROR", "Select a tool first.")
            return
        handler = self.handlers.get(tool.id) or self.handlers.get(tool.category)
        if handler is None:
            self._log("WARNING", f"No processor registered for {tool.id}; connect your existing local function.")
            return
        try:
            request = self._collect_request(tool)
        except (ValueError, OSError) as exc:
            self._log("WARNING", str(exc))
            return
        self.job_status = "RUNNING"
        self.progress_value = 0.0
        self._last_progress_note = f"Running {tool.name}…"
        self.query_one("#progress-note", Static).update(self._last_progress_note)
        self._log("INFO", f"Started {tool.name} with {len(request.paths)} input path(s).")
        self.run_worker(lambda: self._execute_handler(request, handler), name=f"job-{tool.id}", group="processing", exclusive=True, thread=True, exit_on_error=False)

    def _execute_handler(self, request: ToolRequest, handler: Handler) -> None:
        def report_from_worker(percent: float, message: str) -> None:
            try:
                self.call_from_thread(self._on_progress, percent, message)
            except RuntimeError:
                pass
        reporter = ProgressReporter(report_from_worker)
        try:
            result = handler(request, reporter)
        except Exception as exc:
            try:
                self.call_from_thread(self._on_job_finished, False, f"{type(exc).__name__}: {exc}")
            except RuntimeError:
                pass
        else:
            detail = str(result) if result is not None else "Task completed."
            try:
                self.call_from_thread(self._on_job_finished, True, detail)
            except RuntimeError:
                pass

    def _on_progress(self, percent: float, message: str) -> None:
        self.progress_value = percent
        if message:
            self._last_progress_note = message
            self.query_one("#progress-note", Static).update(message)
            self._log("INFO", message)

    def _on_job_finished(self, success: bool, detail: str) -> None:
        if success:
            self.job_status = "SUCCESS"
            self.progress_value = 100.0
            self._last_progress_note = "Completed"
            self._log("SUCCESS", detail)
        else:
            self.job_status = "FAILED"
            self._last_progress_note = "Failed — see execution log"
            self._log("ERROR", detail)
        self.query_one("#progress-note", Static).update(self._last_progress_note)

    def watch_job_status(self, status: str) -> None:
        if not self.is_mounted:
            return
        pill = self.query_one("#status-pill", Static)
        pill.update(f"●  {status}")
        for class_name in ("status-idle", "status-running", "status-success", "status-failed"):
            pill.remove_class(class_name)
        class_name = {"IDLE": "status-idle", "RUNNING": "status-running", "SUCCESS": "status-success", "FAILED": "status-failed"}.get(status, "status-idle")
        pill.add_class(class_name)

    def watch_progress_value(self, value: float) -> None:
        if self.is_mounted:
            self.query_one("#progress", ProgressBar).update(progress=value)

    def watch_active_tool(self, tool_id: str) -> None:
        if self.is_mounted:
            self._update_mode_label()

    def _update_mode_label(self) -> None:
        if not self.is_mounted:
            return
        tool = self._selected_tool()
        category = CATEGORY_BY_ID.get(self.active_category)
        label = category.short_label if category else "OFFLINE"
        mode = f"{label}  ·  {tool.name}" if tool else label
        self.query_one("#mode-label", Static).update(mode)

    def _log(self, level: str, message: str) -> None:
        if not self.is_mounted:
            return
        color = {"INFO": "#8B9CFF", "SUCCESS": "#45C99A", "WARNING": "#F0B96B", "ERROR": "#F07878"}.get(level, "#98A6B8")
        line = Text.assemble((f"[{level}]", f"bold {color}"), (" "), (str(message), "#D5DEEA"))
        self.query_one("#console", RichLog).write(line)

    def action_clear_console(self) -> None:
        self.query_one("#console", RichLog).clear()
        self._log("INFO", "Console cleared.")

    def action_switch_category(self, category_key: str) -> None:
        if category_key not in CATEGORY_BY_ID:
            return
        self.query_one("#category-tabs", Tabs).active = category_key


def launch(handlers: Mapping[str, Handler] | None = None) -> None:
    """Start the TUI with optional local processing handlers."""
    OmniToolsTUI(handlers=handlers).run()
