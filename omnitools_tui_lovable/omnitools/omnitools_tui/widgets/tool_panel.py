from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Input, Label, Select, Static, Switch, Tab, Tabs, TextArea

from ..catalog import CATEGORIES, TOOLS_BY_CATEGORY, ToolSpec


class ToolPanel(Vertical):
    class Changed(Message):
        def __init__(self, category_label: str, tool: Optional[ToolSpec]) -> None:
            super().__init__()
            self.category_label, self.tool = category_label, tool

    class RunRequested(Message):
        pass

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.category_key = CATEGORIES[0].key
        self.tool: Optional[ToolSpec] = None

    def compose(self) -> ComposeResult:
        yield Tabs(*[Tab(c.short_label, id=f"cat-{c.key}") for c in CATEGORIES], id="categories")
        with VerticalScroll(id="form"):
            yield Static("▍TOOL", classes="section-title")
            yield Select([(t.name, t.id) for t in TOOLS_BY_CATEGORY[self.category_key]], id="tool-select", allow_blank=False)
            
            # Input paths section with clean Select Files / Select Folder buttons
            yield Static("▍INPUT PATHS  [#475569](one per line)[/]", classes="section-title", id="paths-title")
            with Horizontal(classes="browse-bar"):
                yield Button("📂 Select Files", id="btn-browse-files", classes="picker-btn")
                yield Button("📁 Select Folder", id="btn-browse-folder", classes="picker-btn")
            yield TextArea(placeholder="Paste or select local file or folder paths here", id="paths")
            
            yield Static("▍OPTIONS", classes="section-title")
            yield Vertical(id="options")
            
            # Output directory section with clean Select Folder button
            yield Static("▍OUTPUT FOLDER  [#475569](optional - default: source folder)[/]", classes="section-title")
            with Horizontal(id="output-row"):
                yield Input(placeholder="/path/to/output", id="output-dir")
                yield Button("📁 Select Folder", id="btn-browse-out", classes="picker-btn")

        yield Button("RUN SELECTED TOOL  [F5]", id="run-btn", variant="success")

    async def on_mount(self) -> None:
        await self._load_category(self.category_key)

    def select_index(self, idx: int) -> None:
        if 0 <= idx < len(CATEGORIES):
            self.query_one(Tabs).active = f"cat-{CATEGORIES[idx].key}"

    def paths(self) -> List[str]:
        raw = self.query_one("#paths", TextArea).text.splitlines()
        return [p.strip().strip('"').strip("'") for p in raw if p.strip()]

    def set_paths(self, new_paths: List[Path | str], append: bool = False) -> None:
        ta = self.query_one("#paths", TextArea)
        current = [p.strip() for p in ta.text.splitlines() if p.strip()] if append else []
        for p in new_paths:
            s = str(p).strip().strip('"').strip("'")
            if s and s not in current:
                current.append(s)
        ta.text = "\n".join(current)

    def set_output_dir(self, out_path: Path | str) -> None:
        self.query_one("#output-dir", Input).value = str(out_path).strip().strip('"').strip("'")

    def output_dir(self) -> Path | None:
        val = self.query_one("#output-dir", Input).value.strip().strip('"').strip("'")
        return Path(val).expanduser() if val else None

    def option_values(self) -> Dict[str, Any]:
        values: Dict[str, Any] = {}
        for w in self.query("#options Switch, #options Input, #options Select"):
            if w.id and w.id.startswith("opt-"):
                key = w.id[4:]
                if isinstance(w, Switch):
                    values[key] = w.value
                elif isinstance(w, Select):
                    values[key] = w.value
                elif isinstance(w, Input):
                    values[key] = w.value
        return values

    def set_busy(self, busy: bool) -> None:
        btn = self.query_one("#run-btn", Button)
        btn.label = "QUEUE ANOTHER RUN  [F5]" if busy else "RUN SELECTED TOOL  [F5]"

    async def _load_category(self, cat_key: str) -> None:
        self.category_key = cat_key
        tools = TOOLS_BY_CATEGORY.get(cat_key, ())
        sel = self.query_one("#tool-select", Select)
        sel.set_options([(t.name, t.id) for t in tools])
        if tools:
            sel.value = tools[0].id
            await self._load_tool(tools[0])

    async def _load_tool(self, tool: ToolSpec) -> None:
        self.tool = tool
        box = self.query_one("#options", Vertical)
        await box.remove_children()
        rows = []
        for field in tool.fields:
            if field.kind == "toggle":
                rows.append(Horizontal(
                    Switch(bool(field.default), id=f"opt-{field.key}"),
                    Label(field.label, classes="opt-toggle-label"),
                    classes="opt-toggle-row"
                ))
            elif field.kind == "choice":
                rows.append(Static(f"▍{field.label.upper()}", classes="opt-field-title"))
                rows.append(Select(
                    [(c, c) for c in field.choices],
                    value=str(field.default),
                    allow_blank=False,
                    id=f"opt-{field.key}",
                    classes="opt-control"
                ))
            elif field.kind == "password":
                rows.append(Static(f"▍{field.label.upper()}", classes="opt-field-title"))
                rows.append(Input(
                    str(field.default or ""),
                    placeholder=field.placeholder or "Enter password",
                    password=True,
                    id=f"opt-{field.key}",
                    classes="opt-control"
                ))
            else:
                rows.append(Static(f"▍{field.label.upper()}", classes="opt-field-title"))
                rows.append(Input(
                    str(field.default or ""),
                    placeholder=field.placeholder or f"Enter {field.label.lower()}",
                    id=f"opt-{field.key}",
                    classes="opt-control"
                ))
        if not rows:
            rows.append(Static("[#475569]No extra options for this tool[/]", classes="opt-empty"))
        await box.mount(*rows)
        cat_spec = next((c for c in CATEGORIES if c.key == self.category_key), None)
        cat_name = cat_spec.short_label if cat_spec else self.category_key.upper()
        self.post_message(self.Changed(cat_name, tool))

    async def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        if event.tab and event.tab.id:
            cat_key = event.tab.id.removeprefix("cat-")
            if cat_key in TOOLS_BY_CATEGORY:
                await self._load_category(cat_key)

    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "tool-select" or event.value is Select.BLANK:
            return
        tools = TOOLS_BY_CATEGORY.get(self.category_key, ())
        for t in tools:
            if t.id == event.value and (self.tool is None or t.id != self.tool.id):
                await self._load_tool(t)

    # ---- Native Windows Explorer dialogs ----------------------------
    def open_windows_file_dialog(self) -> None:
        from .file_picker import open_system_picker
        def run() -> None:
            chosen = open_system_picker(mode="files", title="OmniTools - Select Files")
            if chosen:
                self.app.call_from_thread(self.set_paths, [Path(p) for p in chosen], True)
        self.run_worker(run, thread=True, group="os-picker")

    def open_windows_folder_dialog(self) -> None:
        from .file_picker import open_system_picker
        def run() -> None:
            chosen = open_system_picker(mode="folder", title="OmniTools - Select Folder")
            if chosen:
                self.app.call_from_thread(self.set_paths, [Path(p) for p in chosen], False)
        self.run_worker(run, thread=True, group="os-picker")

    def open_windows_output_folder_dialog(self) -> None:
        from .file_picker import open_system_picker
        def run() -> None:
            chosen = open_system_picker(mode="folder", title="OmniTools - Select Output Folder")
            if chosen:
                self.app.call_from_thread(self.set_output_dir, chosen[0])
        self.run_worker(run, thread=True, group="os-picker")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id == "run-btn":
            self.post_message(self.RunRequested())
        elif btn_id == "btn-browse-files":
            self.open_windows_file_dialog()
        elif btn_id == "btn-browse-folder":
            self.open_windows_folder_dialog()
        elif btn_id == "btn-browse-out":
            self.open_windows_output_folder_dialog()
