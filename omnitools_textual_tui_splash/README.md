# OmniTools Textual TUI

A separate keyboard-first terminal interface for OmniTools, implemented with Textual. It does not replace the CustomTkinter desktop UI; it is a second front end that can call the same local processing functions.

## Layout and navigation

- Header: OmniTools name, active category/tool, and live IDLE/RUNNING/SUCCESS/FAILED status.
- Main split: 60% configuration on the left and 40% rich execution log on the right.
- Left: six category tabs, a tool selector, multiline local input paths, dynamic options, output directory, and Run button.
- Right: timestamp-free streaming RichLog with INFO, SUCCESS, WARNING, and ERROR tags plus progress.
- Footer: Q quit, C clear console, Tab focus traversal, 1-6 category switching, F5 run.

The styling is in omnitools_tui/styles.tcss. Source is split between app.py (Textual UI and worker integration), catalog.py (tool/form schema), and styles.tcss (complete TCSS theme).

## Install and run

From this directory, install the dependency and launch the terminal app:

    python -m pip install -r requirements.txt
    python -m omnitools_tui

Use a modern terminal with at least 90 columns and 28 rows for the full split layout. The TUI is entirely local. Textual and Rich are runtime dependencies; tool handlers remain your own offline functions.

At launch, a centered OmniTools splash appears briefly with the creator name. The default creator name is Kesavaraj Samipillai. Add a GitHub handle only if you set it in your entry point or provide the OMNITOOLS_GITHUB environment variable. You can also override the name with OMNITOOLS_AUTHOR.

    launch(handlers=your_handler_map, brand_name="Your Name", github_id="@your-id")

Press Enter, Space, or Escape to skip the splash. Set show_splash=False to disable it.

## Connect existing processors

Pass a mapping from tool IDs (or category IDs) to synchronous Python functions. A handler runs in a Textual worker thread and receives ToolRequest plus ProgressReporter. Use progress.report(percent, message) during work; never update Textual widgets directly from the handler.

    from omnitools_tui import ProgressReporter, ToolRequest, launch
    from your_image_module import convert_images

    def image_handler(request: ToolRequest, progress: ProgressReporter):
        total = len(request.paths)
        for index, source in enumerate(request.paths, start=1):
            # Call the existing local converter with the request options.
            convert_images(source, request.output_dir, request.options)
            progress.report(index * 100 / total, f"Converted {source.name}")
        return f"Converted {total} image(s)"

    launch(handlers={"images.convert": image_handler})

The UI validates paths and gathers option values, but it intentionally does not claim to implement the conversion, encryption, sorting, or QR engines. Connect your existing backend functions by ID; IDs and fields are listed in omnitools_tui/catalog.py. A handler can also be registered by category key, such as images or pdf.

## Import from an existing main.py

Keep the package folder beside your application entry point, then use:

    from omnitools_tui import launch
    launch(handlers=your_handler_map)

The TUI package and the earlier CustomTkinter package are independent interfaces. They can share backend modules while keeping their UI dependencies and entry points separate.
