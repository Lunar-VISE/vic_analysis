from pathlib import Path

from vic_analysis.ui.model.app_config import AppConfig

m3_cfg = AppConfig(
    home_directory="D:/moon_data/m3/Gruithuisen_Region/M3G_GDOMES_MOSAIC/",
    colormap="crameri:grayc_r",
    starting_image=Path(
        "D:/moon_data/m3/Gruithuisen_Region/M3G_GDOMES_MOSAIC/M3G_GRUIT_RFL.json"
    ),
)

vic_config = AppConfig(
    home_directory="F:/",
    colormap="crameri:grayc_r",
    starting_image="F:/cube_files/panorama_cube.fits",
)

# m3_cfg.to_json(Path(__file__).parent, "config")
vic_config.to_json(Path(__file__).parent, "config")
