# OmniTools UI starter

A modular, dark-slate CustomTkinter desktop interface for the offline OmniTools suite. The package provides category navigation, searchable tool cards, file/folder selection, file metadata rows, per-tool settings, output-folder selection, a live status/progress bar, an expandable activity log, FFmpeg detection, and background-thread execution hooks.

## Install and run

From this directory, install the UI dependencies and launch the window:

    python -m pip install -r requirements.txt
    python -m omnitools_ui

Python 3.10+ is recommended. tkinterdnd2 is optional at runtime: if it is missing, the browse controls still work. Native Tkinter must also be available in your Python installation.

## Connect your existing processors

Handlers are ordinary local Python functions. Register a handler by tool ID (most specific) or category key. It receives an immutable ToolRequest and a ProgressReporter. Call report(percent, message) from the worker function; do not update Tk widgets from a handler.

    from omnitools_ui import ToolRequest, ProgressReporter, launch

    def convert_images(request: ToolRequest, progress: ProgressReporter):
        total = len(request.files)
        for index, source in enumerate(request.files, start=1):
            # Call your existing conversion function here.
            # Your function should respect request.options and request.output_dir.
            progress.report(index * 100 / total, f"Converting {source.name}")
        return f"Processed {total} image(s)"

    launch(handlers={"images.convert": convert_images})

Each handler should validate its inputs, handle collisions safely, and raise an exception on failure. Exceptions are shown in the activity log. A handler result is also shown there when it returns a value. The UI deliberately does not claim to implement the PDF, image, audio, or file-system processing engines; connect the functions already in your project.

Available tool IDs are declared in omnitools_ui/catalog.py. You can add tools there and supply their FieldSpec entries to render matching controls. ToolRequest.options contains the field values keyed by their declared keys; password fields are masked in the window.

## Package map and layout

- omnitools_ui/app.py — window composition, navigation, file queue, settings, worker/event loop, status and logs.
- omnitools_ui/catalog.py — categories, tool definitions, option schemas, request model.
- omnitools_ui/theme.py — palette and typography constants.
- omnitools_ui/__init__.py — public imports; python -m omnitools_ui starts the UI.

Wireframe: fixed left sidebar with search, six categories, and FFmpeg status; main workspace with category tool cards or one selected tool's input, options, and output destination; bottom status strip with IDLE/RUNNING/SUCCESS/FAILED, progress, and a collapsible activity log.

## Palette

Background #0B0F14, sidebar #10151D, panels #151C26, border #273342, primary text #E8EDF4, secondary text #98A6B8, accent #8B9CFF, success #45C99A, warning #F0B96B, error #F07878.

## Integration notes

This is a UI package to copy into your Python project. If you already have a main.py, import launch and call it with your handlers. Keep processor code in your existing modules; for example, import convert_images from your image engine and register it under images.convert. The UI collects paths and options but does not move or modify anything until a handler is registered and invoked.
