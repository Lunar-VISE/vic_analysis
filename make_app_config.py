from pathlib import Path

from vic_analysis.ui.model.app_config import AppConfig

cfg = AppConfig(
    home_directory="D:/moon_data/m3/Gruithuisen_Region/M3G_GDOMES_MOSAIC/",
    colormap="crameri:grayc_r",
    starting_image=Path(
        "D:/moon_data/m3/Gruithuisen_Region/M3G_GDOMES_MOSAIC/M3G_GRUIT_RFL.json"
    ),
)

cfg.to_json(Path(__file__).parent, "config")
