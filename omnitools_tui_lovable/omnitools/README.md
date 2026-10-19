# OmniTools TUI

Full-screen Textual interface for the OmniTools offline developer suite.

## Install & run
```bash
pip install -e .
omnitools            # or: python -m omnitools_tui
```
Live CSS editing: `textual run --dev omnitools_tui.app:OmniToolsApp`

## Layout
```
+-------------------------------- Header (dock top) -------------------------------+
| OMNITOOLS        PDF > Merge PDFs                                     [ IDLE ]   |
+---------------- Left 50% ---------------+---------------- Right 50% --------------+
| [PDF][DOCS][IMAGES][MEDIA][SORTER][UTILS]| Execution Log (RichLog)                 |
| Tool  [Select v]                         |  12:00:01 [INFO] ...                    |
| Paths [TextArea]                         |                                         |
| Options (switches / inputs)              +-----------------------------------------+
| [ RUN SELECTED TOOL [F5] ] (docked)      | Task name     ETA 00:12   Queued: 2    |
|                                          | [██████████████░░░░░░░░░░░░░░░] 48%     |
+------------------------------------------+-----------------------------------------+
| Footer: Q Quit  C Clear  Tab Focus  1-6 Tabs  F5 Run                             |
```

## Plugging in real tools
Edit `omnitools_tui/tools.py`. Each `Tool` has an async `run(ctx)` callable that receives
`ctx.log(level, msg)` and `ctx.progress(done, total)`. Replace `demo_job` with your real
implementations (run blocking work via `asyncio.to_thread`).

## Package map
- `app.py` - App composition, bindings, queue/worker execution
- `theme.tcss` - Cyberpunk / Dark Slate theme (zero-gap layout)
- `tools.py` - Category + tool registry and option schema
- `widgets/` - `OmniHeader`, `ToolPanel`, `LogPanel`, `ProgressCard`
