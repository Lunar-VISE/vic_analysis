import unittest

import numpy as np

from vic_analysis.stitching.image_geometry import GeometricImage


class GeometricImageTests(unittest.TestCase):
    def test_from_image_aligns_row_major_values_with_xy_coordinates(self) -> None:
        pixels = np.array([[0, 1, 2], [10, 11, 12]])

        image = GeometricImage.from_image(pixels, topmost_pixel=5, leftmost_pixel=7)

        np.testing.assert_array_equal(image.values, pixels.ravel())
        np.testing.assert_array_equal(
            image.pixel_coords,
            [[7, 5], [8, 5], [9, 5], [7, 6], [8, 6], [9, 6]],
        )
        np.testing.assert_array_equal(image.to_image(), pixels)


if __name__ == "__main__":
    unittest.main()
