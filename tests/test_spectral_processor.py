import unittest

import numpy as np
from scipy.ndimage import uniform_filter1d

from vic_analysis.ui.model.spectral_processor import (
    FilterParameters,
    FilterType,
    GaussianParameters,
    NormalizeParameters,
    ProcessingOperation,
    SpectralProcessor,
    UniformParameters,
)


class SpectralProcessorTests(unittest.TestCase):
    def test_run_recomputes_enabled_steps_from_original_spectrum(self) -> None:
        source = np.array([2.0, 4.0, 8.0, 16.0])
        processor = SpectralProcessor(source)
        normalization_id = processor.add_normalization_step(0)
        filter_id = processor.add_filter_step(
            FilterType.UNIFORM, UniformParameters(size=3)
        )

        normalized = source / source[0]
        expected = uniform_filter1d(normalized, size=3)
        np.testing.assert_allclose(processor.run(), expected)
        np.testing.assert_array_equal(source, [2.0, 4.0, 8.0, 16.0])

        processor.set_step_enabled(normalization_id, False)
        processor.update_step_parameters(
            filter_id,
            FilterParameters(FilterType.GAUSSIAN, GaussianParameters(sigma=1)),
        )
        actual = processor.run()
        self.assertFalse(np.array_equal(actual, expected))

        processor.set_step_enabled(normalization_id, True)
        processor.update_step_parameters(
            filter_id,
            FilterParameters(FilterType.UNIFORM, UniformParameters(size=3)),
        )
        np.testing.assert_allclose(processor.run(), expected, rtol=1e-6)

    def test_steps_can_be_removed_and_unknown_ids_are_rejected(self) -> None:
        processor = SpectralProcessor(np.array([1.0, 2.0, 3.0]))
        step_id = processor.add_normalization_step(0, step_id="normalize")
        processor.remove_step(step_id)

        self.assertEqual(processor.steps, ())
        np.testing.assert_array_equal(processor.run(), [1.0, 2.0, 3.0])
        with self.assertRaises(KeyError):
            processor.set_step_enabled(step_id, False)

    def test_step_parameter_types_must_match_operation(self) -> None:
        processor = SpectralProcessor(np.array([1.0, 2.0, 3.0]))
        step_id = processor.add_normalization_step(0)

        with self.assertRaises(TypeError):
            processor.update_step_parameters(
                step_id, UniformParameters(size=3)
            )
        with self.assertRaises(TypeError):
            processor.add_step(
                ProcessingOperation.FILTER,
                NormalizeParameters(band_index=0),
            )

    def test_run_without_input_spectrum_fails_explicitly(self) -> None:
        processor = SpectralProcessor()

        with self.assertRaisesRegex(TypeError, "Spectrum has not been set"):
            processor.run()


if __name__ == "__main__":
    unittest.main()
