from importlib.resources import files
from pathlib import Path

QTADS_STYLE = str(files("vic_analysis").joinpath("resources/qtads_style.qss"))
QT_STYLE = str(files("vic_analysis").joinpath("resources/qt_style.qss"))


def load_stylesheet(fp: Path | str) -> str:
    """Load a Qt Stylesheet from .qss file"""
    with open(fp, "r") as f:
        return f.read()
