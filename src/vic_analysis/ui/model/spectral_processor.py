from dataclasses import dataclass
from enum import StrEnum, auto
from uuid import uuid4

import numpy as np
from scipy.ndimage import gaussian_filter1d, uniform_filter1d
from scipy.signal import savgol_filter


class FilterType(StrEnum):
    UNIFORM = auto()
    GAUSSIAN = auto()
    SAVGOL = auto()


class ProcessingOperation(StrEnum):
    NORMALIZE_TO_BAND = auto()
    FILTER = auto()


@dataclass(frozen=True)
class UniformParameters:
    size: int


@dataclass(frozen=True)
class GaussianParameters:
    sigma: int


@dataclass(frozen=True)
class SavgolParameters:
    window_length: int
    polyorder: int


type FilterParameterSet = UniformParameters | GaussianParameters | SavgolParameters


@dataclass(frozen=True)
class NormalizeParameters:
    band_index: int


@dataclass(frozen=True)
class FilterParameters:
    filter_type: FilterType
    filter_params: FilterParameterSet


type StepParameters = NormalizeParameters | FilterParameters


@dataclass(frozen=True)
class ProcessingStep:
    step_id: str
    operation: ProcessingOperation
    parameters: StepParameters
    enabled: bool = True


class SpectralProcessor:
    """Runs an ordered, configurable processing pipeline on a spectrum."""

    def __init__(self, spectrum: np.ndarray | None = None) -> None:
        self._original_spectrum: np.ndarray | None = None
        self._spectrum: np.ndarray | None = None
        self._steps: list[ProcessingStep] = []
        if spectrum is not None:
            self.spectrum = spectrum

    @property
    def steps(self) -> tuple[ProcessingStep, ...]:
        """The configured steps in processing order."""
        return tuple(self._steps)

    def add_normalization_step(
        self,
        band_index: int,
        *,
        enabled: bool = True,
        step_id: str | None = None,
    ) -> str:
        return self.add_step(
            ProcessingOperation.NORMALIZE_TO_BAND,
            NormalizeParameters(band_index),
            enabled=enabled,
            step_id=step_id,
        )

    def add_filter_step(
        self,
        filter_type: FilterType,
        filter_params: FilterParameterSet,
        *,
        enabled: bool = True,
        step_id: str | None = None,
    ) -> str:
        return self.add_step(
            ProcessingOperation.FILTER,
            FilterParameters(filter_type, filter_params),
            enabled=enabled,
            step_id=step_id,
        )

    def add_step(
        self,
        operation: ProcessingOperation,
        parameters: StepParameters,
        *,
        enabled: bool = True,
        step_id: str | None = None,
    ) -> str:
        self._validate_parameters(operation, parameters)
        step_id = step_id or str(uuid4())
        if any(step.step_id == step_id for step in self._steps):
            raise ValueError(f"Processing step ID already exists: {step_id}")
        self._steps.append(ProcessingStep(step_id, operation, parameters, enabled))
        return step_id

    def remove_step(self, step_id: str) -> None:
        index = self._step_index(step_id)
        del self._steps[index]

    def set_step_enabled(self, step_id: str, enabled: bool) -> None:
        index = self._step_index(step_id)
        step = self._steps[index]
        self._steps[index] = ProcessingStep(
            step.step_id, step.operation, step.parameters, enabled
        )

    def update_step_parameters(self, step_id: str, parameters: StepParameters) -> None:
        index = self._step_index(step_id)
        step = self._steps[index]
        self._validate_parameters(step.operation, parameters)
        self._steps[index] = ProcessingStep(
            step.step_id, step.operation, parameters, step.enabled
        )

    def _step_index(self, step_id: str) -> int:
        for index, step in enumerate(self._steps):
            if step.step_id == step_id:
                return index
        raise KeyError(f"Unknown processing step ID: {step_id}")

    @staticmethod
    def _validate_parameters(
        operation: ProcessingOperation, parameters: StepParameters
    ) -> None:
        if operation == ProcessingOperation.NORMALIZE_TO_BAND:
            if not isinstance(parameters, NormalizeParameters):
                raise TypeError("Normalization steps require NormalizeParameters.")
            return
        if operation == ProcessingOperation.FILTER:
            if not isinstance(parameters, FilterParameters):
                raise TypeError("Filter steps require FilterParameters.")
            SpectralProcessor._validate_filter_parameters(
                parameters.filter_type, parameters.filter_params
            )
            return
        raise ValueError(f"Unsupported processing operation: {operation}")

    @staticmethod
    def _validate_filter_parameters(
        filter_type: FilterType, filter_params: FilterParameterSet
    ) -> None:
        expected_type = {
            FilterType.UNIFORM: UniformParameters,
            FilterType.GAUSSIAN: GaussianParameters,
            FilterType.SAVGOL: SavgolParameters,
        }.get(filter_type)
        if expected_type is None:
            raise ValueError(f"Unsupported filter type: {filter_type}")
        if not isinstance(filter_params, expected_type):
            raise TypeError("Invalid parameter set for chosen filter.")

    def normalize_to_band(self, band_index: int) -> None:
        self.spectrum = self._normalize(self.spectrum, band_index)

    def filter(
        self, filter_type: FilterType, filter_params: FilterParameterSet
    ) -> None:
        self.spectrum = self._filter(self.spectrum, filter_type, filter_params)

    @staticmethod
    def _normalize(spectrum: np.ndarray, band_index: int) -> np.ndarray:
        return spectrum / spectrum[band_index]

    @staticmethod
    def _filter(
        spectrum: np.ndarray,
        filter_type: FilterType,
        filter_params: FilterParameterSet,
    ) -> np.ndarray:
        SpectralProcessor._validate_filter_parameters(filter_type, filter_params)
        match filter_type:
            case FilterType.UNIFORM:
                assert isinstance(filter_params, UniformParameters)
                return uniform_filter1d(input=spectrum, size=filter_params.size)
            case FilterType.GAUSSIAN:
                assert isinstance(filter_params, GaussianParameters)
                return gaussian_filter1d(input=spectrum, sigma=filter_params.sigma)
            case FilterType.SAVGOL:
                assert isinstance(filter_params, SavgolParameters)
                return savgol_filter(
                    x=spectrum,
                    window_length=filter_params.window_length,
                    polyorder=filter_params.polyorder,
                )
        raise ValueError(f"Unsupported filter type: {filter_type}")

    def run(self) -> np.ndarray:
        """Recompute and return the output from the original input spectrum."""
        result = self._require_original_spectrum().copy()
        for step in self._steps:
            if not step.enabled:
                continue
            if step.operation == ProcessingOperation.NORMALIZE_TO_BAND:
                if not isinstance(step.parameters, NormalizeParameters):
                    raise TypeError("Normalization steps require NormalizeParameters.")
                result = self._normalize(result, step.parameters.band_index)
            elif step.operation == ProcessingOperation.FILTER:
                if not isinstance(step.parameters, FilterParameters):
                    raise TypeError("Filter steps require FilterParameters.")
                result = self._filter(
                    result,
                    step.parameters.filter_type,
                    step.parameters.filter_params,
                )
            else:
                raise ValueError(f"Unsupported processing operation: {step.operation}")
        self._spectrum = result
        return result

    @property
    def spectrum(self) -> np.ndarray:
        if self._spectrum is None:
            raise TypeError("Spectrum has not been set for processor.")
        return self._spectrum

    @spectrum.setter
    def spectrum(self, val: np.ndarray) -> None:
        self._original_spectrum = np.asarray(val).copy()
        self._spectrum = self._original_spectrum.copy()

    def _require_original_spectrum(self) -> np.ndarray:
        if self._original_spectrum is None:
            raise TypeError("Spectrum has not been set for processor.")
        return self._original_spectrum
