import numpy as np
from scipy.interpolate import PchipInterpolator


class SpectralResponseFunction:
    def __init__(self, response: np.ndarray, wavelength: np.ndarray) -> None:
        self.rsp = response
        self.wvl = wavelength
        self._interp = PchipInterpolator(self.wvl, self.rsp)

    def crop_to_wavelengths(self, min_wvl: float, max_wvl: float) -> None:
        mask = (self.wvl > min_wvl) & (self.wvl < max_wvl)
        self.rsp = self.rsp[mask]
        self.wvl = self.wvl[mask]

    def _interpolate_to_new_wavelengths(self, target_wavelengths: np.ndarray) -> None:
        self.rsp = self._interp(target_wavelengths)
        self.wvl = target_wavelengths

    def get_band_value(
        self, reference_spectrum: np.ndarray, reference_wavelengths: np.ndarray
    ) -> tuple[float, float]:
        """Get band value and wavelength value."""
        self._interpolate_to_new_wavelengths(reference_wavelengths)
        if self.rsp.size != reference_spectrum.size:
            raise ValueError("Invalid Response Shape.")
        band_val: float = np.average(reference_spectrum, weights=self.rsp)
        wvl_val: float = np.average(reference_wavelengths, weights=self.rsp)
        return band_val, wvl_val


class InstrumentResponse:
    def __init__(self):
        self.band_responses: list[SpectralResponseFunction] = []

    def add_response(self, response: np.ndarray | SpectralResponseFunction) -> None:
        if isinstance(response, np.ndarray):
            srf = SpectralResponseFunction(response[:, 1], response[:, 0])
        elif isinstance(response, SpectralResponseFunction):
            srf = response
        self.band_responses.append(srf)

    def resample_spectrum(
        self, spectrum: np.ndarray, wavelength: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Resample a spectrum to added response functions."""
        resampled_spectrum = np.empty(len(self.band_responses))
        resampled_wavelength = np.empty_like(resampled_spectrum)
        for n, response in enumerate(self.band_responses):
            spec_val, wvl_val = response.get_band_value(spectrum, wavelength)
            resampled_spectrum[n] = spec_val
            resampled_wavelength[n] = wvl_val
        return resampled_wavelength, resampled_spectrum
