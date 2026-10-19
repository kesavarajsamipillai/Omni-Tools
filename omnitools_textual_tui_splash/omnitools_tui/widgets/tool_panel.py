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
            yield Static("▍INPUT PATHS  [#475569](one per line)[/]", classes="section-title", id="paths-title")
            yield TextArea(placeholder="Paste local file or folder paths here (one per line)", id="paths")
            yield Static("▍OPTIONS", classes="section-title")
            yield Vertical(id="options")
            yield Static("▍OUTPUT FOLDER  [#475569](optional - default: source folder)[/]", classes="section-title")
            yield Input(placeholder="/path/to/output", id="output-dir")
        yield Button("RUN SELECTED TOOL  [F5]", id="run-btn", variant="success")

    def on_mount(self) -> None:
        self._load_category(self.category_key)

    def select_index(self, idx: int) -> None:
        if 0 <= idx < len(CATEGORIES):
            self.query_one(Tabs).active = f"cat-{CATEGORIES[idx].key}"

    def paths(self) -> List[str]:
        raw = self.query_one("#paths", TextArea).text.splitlines()
        return [p.strip().strip('"').strip("'") for p in raw if p.strip()]

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

    def _load_category(self, cat_key: str) -> None:
        self.category_key = cat_key
        tools = TOOLS_BY_CATEGORY.get(cat_key, ())
        sel = self.query_one("#tool-select", Select)
        sel.set_options([(t.name, t.id) for t in tools])
        if tools:
            sel.value = tools[0].id
            self._load_tool(tools[0])

    def _load_tool(self, tool: ToolSpec) -> None:
        self.tool = tool
        box = self.query_one("#options", Vertical)
        box.remove_children()
        rows = []
        for field in tool.fields:
            if field.kind == "toggle":
                rows.append(Horizontal(
                    Switch(bool(field.default), id=f"opt-{field.key}"),
                    Label(field.label),
                    classes="opt-row"
                ))
            elif field.kind == "choice":
                rows.append(Horizontal(
                    Label(field.label, classes="opt-label"),
                    Select([(c, c) for c in field.choices], value=str(field.default), allow_blank=False, id=f"opt-{field.key}"),
                    classes="opt-row"
                ))
            elif field.kind == "password":
                rows.append(Horizontal(
                    Label(field.label, classes="opt-label"),
                    Input(str(field.default or ""), placeholder=field.placeholder or "Password", password=True, id=f"opt-{field.key}"),
                    classes="opt-row"
                ))
            else:
                rows.append(Horizontal(
                    Label(field.label, classes="opt-label"),
                    Input(str(field.default or ""), placeholder=field.placeholder, id=f"opt-{field.key}"),
                    classes="opt-row"
                ))
        if not rows:
            rows.append(Static("[#475569]No extra options for this tool[/]", classes="opt-empty"))
        box.mount(*rows)
        cat_spec = next((c for c in CATEGORIES if c.key == self.category_key), None)
        cat_name = cat_spec.short_label if cat_spec else self.category_key.upper()
        self.post_message(self.Changed(cat_name, tool))

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        if event.tab and event.tab.id:
            cat_key = event.tab.id.removeprefix("cat-")
            if cat_key in TOOLS_BY_CATEGORY:
                self._load_category(cat_key)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "tool-select" or event.value is Select.BLANK:
            return
        tools = TOOLS_BY_CATEGORY.get(self.category_key, ())
        for t in tools:
            if t.id == event.value and (self.tool is None or t.id != self.tool.id):
                self._load_tool(t)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-btn":
            self.post_message(self.RunRequested())
