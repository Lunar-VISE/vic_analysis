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
