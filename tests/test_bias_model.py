import unittest

import numpy as np

from vic_analysis.radiance_pipeline.bias_model import BayerPattern


class BayerPatternTests(unittest.TestCase):
    def test_iter_from_array_yields_patterns_in_row_major_cell_order(self) -> None:
        values = np.arange(4 * 8).reshape(4, 8)

        patterns = list(BayerPattern.iter_from_array(values))

        self.assertEqual(
            patterns,
            [
                BayerPattern(0, 2, 1, 8, 3, 10, 9, 11),
                BayerPattern(4, 6, 5, 12, 7, 14, 13, 15),
                BayerPattern(16, 18, 17, 24, 19, 26, 25, 27),
                BayerPattern(20, 22, 21, 28, 23, 30, 29, 31),
            ],
        )

    def test_iter_from_array_rejects_dimensions_without_full_cells(self) -> None:
        for shape in ((3, 8), (4, 6), (0, 8), (4, 0)):
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                BayerPattern.iter_from_array(np.empty(shape))

    def test_iter_from_array_rejects_non_2d_arrays(self) -> None:
        with self.assertRaises(ValueError):
            BayerPattern.iter_from_array(np.empty(8))


if __name__ == "__main__":
    unittest.main()
