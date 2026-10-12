import tempfile
import unittest
from pathlib import Path

import numpy as np
from astropy.io import fits

from vic_analysis.read.cube_format import CubeFormat
from vic_analysis.read.image_pyramid import ImagePyramid
from vic_analysis.ui.model.image_data import ImageData


def downsample(image: np.ndarray) -> np.ndarray:
    padded = np.full(
        (image.shape[0] + image.shape[0] % 2, image.shape[1] + image.shape[1] % 2),
        np.nan,
    )
    padded[: image.shape[0], : image.shape[1]] = image
    blocks = padded.reshape(
        padded.shape[0] // 2, 2, padded.shape[1] // 2, 2
    )
    valid = ~np.isnan(blocks)
    totals = np.where(valid, blocks, 0).sum(axis=(1, 3))
    counts = valid.sum(axis=(1, 3))
    return np.divide(
        totals,
        counts,
        out=np.full(totals.shape, np.nan),
        where=counts > 0,
    )


class ImagePyramidTests(unittest.TestCase):
    def test_image_data_windows_preserve_all_cube_axis_orders(self) -> None:
        canonical = np.arange(7 * 9 * 3).reshape(7, 9, 3)

        for image_format in (
            CubeFormat.RCB,
            CubeFormat.RBC,
            CubeFormat.BRC,
            CubeFormat.BCR,
            CubeFormat.CRB,
            CubeFormat.CBR,
        ):
            with self.subTest(image_format=image_format):
                source = CubeFormat.RCB.convert_to(canonical, image_format)
                image_data = ImageData(source, image_format)

                np.testing.assert_array_equal(
                    image_data.read_window(2, 1, 6, 2, 8),
                    canonical[1:6, 2:8, 2],
                )
                np.testing.assert_array_equal(
                    image_data.sample_band(2), canonical[:, :, 2]
                )

    def test_builds_and_reads_tiled_overviews_for_rcb_source(self) -> None:
        rows, cols, bands = 521, 527, 2
        source = np.arange(rows * cols * bands, dtype=np.float32).reshape(
            rows, cols, bands
        )
        source[0:2, 0:2, 1] = np.nan
        image_data = ImageData(source, CubeFormat.RCB)

        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "cube.bip"
            source_path.write_bytes(b"source")
            pyramid = ImagePyramid.ensure(source_path, image_data)

            self.assertEqual(pyramid.path, source_path.with_suffix(".bip.pyr"))
            self.assertEqual(pyramid.max_level, 2)

            expected = source[:, :, 1]
            for level in range(1, pyramid.max_level + 1):
                expected = downsample(expected)
                actual = pyramid.read_region(
                    1, level, 0, expected.shape[0], 0, expected.shape[1]
                )
                np.testing.assert_allclose(actual, expected, equal_nan=True)

            partial = pyramid.read_region(1, 1, 200, 270, 240, 270)
            np.testing.assert_allclose(
                partial, downsample(source[:, :, 1])[200:270, 240:270], equal_nan=True
            )

    def test_reads_brc_source_in_row_column_order(self) -> None:
        source = np.arange(2 * 513 * 519, dtype=np.float32).reshape(2, 513, 519)
        image_data = ImageData(source, CubeFormat.BRC)

        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "cube.fits"
            source_path.write_bytes(b"source")
            pyramid = ImagePyramid.ensure(source_path, image_data)

            actual = pyramid.read_region(1, 1, 40, 80, 100, 140)
            expected = downsample(source[1])[40:80, 100:140]
            np.testing.assert_allclose(actual, expected, equal_nan=True)

    def test_finds_empty_bands_without_creating_overview_levels(self) -> None:
        source = np.full((20, 30, 3), np.nan, dtype=np.float32)
        source[:, :, 1] = 1
        source[0, 0, 2] = np.inf
        image_data = ImageData(source, CubeFormat.RCB)

        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "small.bip"
            source_path.write_bytes(b"source")
            pyramid = ImagePyramid.ensure(source_path, image_data)

            np.testing.assert_array_equal(
                pyramid.find_nan_bands(image_data), np.array([True, False, False])
            )

    def test_load_data_creates_sidecar_and_keeps_fits_disk_backed(self) -> None:
        from vic_analysis.read.data_loader import load_data

        source = np.ones((2, 513, 519), dtype=np.float32)

        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "cube.fits"
            fits.PrimaryHDU(source).writeto(source_path)

            image_data = load_data(source_path)

            self.assertFalse(image_data.array.flags.owndata)
            self.assertEqual(image_data.source_path, source_path)
            self.assertTrue(source_path.with_suffix(".fits.pyr").is_file())
            np.testing.assert_array_equal(image_data.nan_bands, [False, False])
            del image_data


if __name__ == "__main__":
    unittest.main()
