import re
from importlib.resources import files
from pathlib import Path
from uuid import uuid4

import matplotlib.pyplot as plt
from cmap import Colormap
from matplotlib.axes import Axes

from vic_analysis.vic_spectral_response import get_vic_band_responses
from vic_analysis.write.spectrum_model import (
    FullSpectrumModel,
    SpectrumArea,
)

from .spectrum_resampler import InstrumentResponse

stylesheet = str(files("vic_analysis").joinpath("resources/publications.mplstyle"))
plt.style.use(stylesheet)
import numpy as np


def load_spectrum_from_txt(filepath: str | Path) -> FullSpectrumModel:
    arr = np.loadtxt(filepath, skiprows=1)
    return FullSpectrumModel.build(arr, np.array([[0, 0]]), uuid4())


def load_saved_spectrum(filepath: Path | str) -> SpectrumArea:
    with open(filepath, "r") as f:
        return SpectrumArea.model_validate_json(f.read())


def load_saved_spectrum_directory(spectrum_directory: Path | str) -> list[SpectrumArea]:
    if not (spectrum_directory := Path(spectrum_directory)).is_dir():
        raise ValueError(f"Path is not a directory: {spectrum_directory}")
    spec_list = []
    for file in spectrum_directory.iterdir():
        if file.suffix != ".json":
            continue
        spec_list.append(load_saved_spectrum(file))

    return spec_list


def plot_spectra(
    spectra: list[SpectrumArea], single_color: str | None = None, ax: Axes | None = None
) -> None:
    if ax is None:
        _f, ax = plt.subplots()
    clrmap = Colormap("seaborn:tab20")
    for n, spec in enumerate(spectra):
        if single_color is None:
            color = clrmap.to_mpl()(n)
        else:
            color = single_color
        ax.plot(
            spec.wavelength.values,
            spec.mean_spectrum,
            label=spec.name,
            color=color,
            marker="x",
        )
    ax.set(xlabel="Wavelength (nm)", ylabel="Radiance (W/m^2-sr-\u03bcm)")
    ax.legend()


def _extract_reflectance_from_name(name: str) -> float:
    res = re.match(r"spectralon_(\d+.?\d+)", name)
    if res is None:
        raise ValueError(f"Invalid name: {name}")
    return float(res.groups()[0]) / 100


def scale_spectra_to_unity_reflectance(spectra: list[SpectrumArea]):
    for spectrum in spectra:
        scaled = [
            i / _extract_reflectance_from_name(spectrum.name)
            for i in spectrum.mean_spectrum
        ]
        spectrum.mean_spectrum = scaled


def get_spectralon_reflectance():
    """Returns spectral (wvl, rfl)"""
    vic_response = InstrumentResponse()
    for rsp in get_vic_band_responses(400, 1000):
        vic_response.add_response(rsp)
    spec = load_spectrum_from_txt(
        "D:/panorama_testing/spectralon_reflectance/USGS_splib07b_Spectralon99.txt"
    )
    specvals = np.array(spec.values)
    wvlvals = np.array(spec.wavelength.values) * 1000
    return vic_response.resample_spectrum(specvals, wvlvals)


def get_halogen_source(spectra: list[SpectrumArea]) -> np.ndarray:
    _, spectralon_reflectance = get_spectralon_reflectance()
    halogen_source_samples = []
    for spectrum in spectra:
        halogen_source_samples.append(
            np.array(spectrum.mean_spectrum) / spectralon_reflectance
        )
    return np.column_stack(halogen_source_samples).mean(axis=1)


def main(scale_to_unity: bool = False):
    spectra = load_saved_spectrum_directory(
        "D:/panorama_testing/vic_pano3_100726_55degrees/spectralon_targets/"
    )
    if scale_to_unity:
        scale_spectra_to_unity_reflectance(spectra)
    halogen_source_spectra = get_halogen_source(spectra)

    _f, ax = plt.subplots()
    plot_spectra(spectra, ax=ax)
    ax.plot(spectra[0].wavelength.values, halogen_source_spectra, color="g", lw=4)


if __name__ == "__main__":
    main(scale_to_unity=True)
    plt.show()
