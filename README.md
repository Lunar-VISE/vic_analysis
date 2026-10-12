## VIC Analysis

### Run the application

```powershell
uv run vic-analysis
```

### UI structure

- `vic_analysis.ui.application` owns Qt application creation and startup.
- `vic_analysis.ui.main_window` owns the top-level window shell.
- `vic_analysis.ui.views` contains screen-level views such as the dashboard.
- `vic_analysis.ui.styles` contains shared application styling.

Keep feature-specific widgets close to their view, and keep reusable widgets in a
dedicated `ui/widgets` package as the interface grows.

### Image pyramids

Opening a supported image creates or refreshes a sibling `<source filename>.pyr`
file. The `.pyr` is a compressed, tiled SQLite cache used by this application; it
is not an ArcGIS Pro interchange format. Panning and zooming read only the
visible source window or overview tiles. The first open builds the pyramid
synchronously, while later opens reuse it. The cache is rebuilt when the source
file or its source metadata/data dependencies change. Color-limit and histogram
statistics use a regular sample capped at one million pixels per band to avoid
materializing whole image planes in memory.
