from __future__ import annotations

import math
import os
import sqlite3
import zlib
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

import numpy as np

if TYPE_CHECKING:
    from vic_analysis.ui.model.image_data import ImageData

_TILE_SIZE = 256
_FORMAT_VERSION = "2"


def _downsample(image: np.ndarray) -> np.ndarray:
    height, width = image.shape
    padded = np.full(
        (height + height % 2, width + width % 2),
        np.nan,
        dtype=np.result_type(image.dtype, np.float32),
    )
    padded[:height, :width] = image
    blocks = padded.reshape(padded.shape[0] // 2, 2, padded.shape[1] // 2, 2)
    finite = np.isfinite(blocks)
    totals = np.where(finite, blocks, 0).sum(axis=(1, 3))
    counts = finite.sum(axis=(1, 3))
    return np.divide(
        totals,
        counts,
        out=np.full(
            totals.shape, np.nan, dtype=np.result_type(image.dtype, np.float32)
        ),
        where=counts > 0,
    )


class ImagePyramid:
    """Tiled, disk-backed overview levels for a source image cube."""

    def __init__(
        self,
        path: Path,
        rows: int,
        cols: int,
        bands: int,
        max_level: int,
        tile_size: int = _TILE_SIZE,
    ) -> None:
        self.path = path
        self.rows = rows
        self.cols = cols
        self.bands = bands
        self.max_level = max_level
        self.tile_size = tile_size

    @classmethod
    def ensure(cls, source_path: Path, image_data: ImageData) -> ImagePyramid:
        source_stat = source_path.stat()
        rows = image_data.format.nrows(image_data.array.shape)
        cols = image_data.format.ncols(image_data.array.shape)
        bands = image_data.format.nbands(image_data.array.shape)
        expected = {
            "version": _FORMAT_VERSION,
            "source_size": str(source_stat.st_size),
            "source_mtime_ns": str(source_stat.st_mtime_ns),
            "rows": str(rows),
            "cols": str(cols),
            "bands": str(bands),
            "source_dtype": image_data.array.dtype.str,
            "tile_size": str(_TILE_SIZE),
            "dependency_count": str(len(image_data.source_dependencies)),
        }
        for index, dependency in enumerate(image_data.source_dependencies):
            print(dependency)
            dependency_stat = dependency.stat()
            expected[f"dependency_{index}_path"] = str(dependency.resolve())
            expected[f"dependency_{index}_size"] = str(dependency_stat.st_size)
            expected[f"dependency_{index}_mtime_ns"] = str(dependency_stat.st_mtime_ns)
        path = source_path.with_suffix(source_path.suffix + ".pyr")

        if path.exists():
            with closing(sqlite3.connect(path)) as connection:
                metadata = dict(connection.execute("SELECT key, value FROM metadata"))
            if all(metadata.get(key) == value for key, value in expected.items()):
                max_level = int(metadata["max_level"])
                return cls(path, rows, cols, bands, max_level)

        cls._build(path, image_data, expected)
        with closing(sqlite3.connect(path)) as connection:
            metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        return cls(path, rows, cols, bands, int(metadata["max_level"]))

    @classmethod
    def _build(
        cls,
        path: Path,
        image_data: ImageData,
        metadata: dict[str, str],
    ) -> None:
        rows = image_data.format.nrows(image_data.array.shape)
        cols = image_data.format.ncols(image_data.array.shape)
        bands = image_data.format.nbands(image_data.array.shape)
        max_level = 0
        level_rows, level_cols = rows, cols
        while max(level_rows, level_cols) > _TILE_SIZE:
            level_rows = (level_rows + 1) // 2
            level_cols = (level_cols + 1) // 2
            max_level += 1

        temp_path = path.with_name(f"{path.name}.{uuid4().hex}.tmp")
        try:
            with closing(sqlite3.connect(temp_path)) as connection, connection:
                connection.execute("PRAGMA journal_mode = OFF")
                connection.execute("PRAGMA synchronous = OFF")
                connection.execute(
                    "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
                )
                connection.execute(
                    """
                    CREATE TABLE tiles (
                        level INTEGER NOT NULL,
                        band INTEGER NOT NULL,
                        tile_row INTEGER NOT NULL,
                        tile_col INTEGER NOT NULL,
                        data BLOB NOT NULL,
                        PRIMARY KEY (level, band, tile_row, tile_col)
                    )
                    """
                )
                metadata["max_level"] = str(max_level)
                connection.executemany(
                    "INSERT INTO metadata (key, value) VALUES (?, ?)",
                    metadata.items(),
                )

                previous_rows, previous_cols = rows, cols
                for level in range(1, max_level + 1):
                    out_rows = (previous_rows + 1) // 2
                    out_cols = (previous_cols + 1) // 2
                    dtype = np.dtype(np.result_type(image_data.array.dtype, np.float32))
                    previous_dtype = (
                        image_data.array.dtype
                        if level == 1
                        else np.dtype(
                            dict(connection.execute("SELECT key, value FROM metadata"))[
                                f"dtype_{level - 1}"
                            ]
                        )
                    )
                    connection.execute(
                        "INSERT INTO metadata (key, value) VALUES (?, ?)",
                        (f"dtype_{level}", dtype.str),
                    )

                    for band in range(bands):
                        has_non_nan_pixels = False
                        has_finite_pixels = False
                        for row_start in range(0, out_rows, _TILE_SIZE):
                            row_stop = min(row_start + _TILE_SIZE, out_rows)
                            for col_start in range(0, out_cols, _TILE_SIZE):
                                col_stop = min(col_start + _TILE_SIZE, out_cols)
                                source_row_start = row_start * 2
                                source_row_stop = min(row_stop * 2, previous_rows)
                                source_col_start = col_start * 2
                                source_col_stop = min(col_stop * 2, previous_cols)

                                if level == 1:
                                    source = image_data.read_window(
                                        band,
                                        source_row_start,
                                        source_row_stop,
                                        source_col_start,
                                        source_col_stop,
                                    )
                                    has_non_nan_pixels |= not np.isnan(source).all()
                                    has_finite_pixels |= np.isfinite(source).any()
                                else:
                                    source = cls._read_region(
                                        connection,
                                        band,
                                        level - 1,
                                        source_row_start,
                                        source_row_stop,
                                        source_col_start,
                                        source_col_stop,
                                        previous_rows,
                                        previous_cols,
                                        _TILE_SIZE,
                                        previous_dtype,
                                    )

                                downsampled = _downsample(source)
                                connection.execute(
                                    """
                                    INSERT INTO tiles
                                        (level, band, tile_row, tile_col, data)
                                    VALUES (?, ?, ?, ?, ?)
                                    """,
                                    (
                                        level,
                                        band,
                                        row_start // _TILE_SIZE,
                                        col_start // _TILE_SIZE,
                                        zlib.compress(downsampled.tobytes()),
                                    ),
                                )

                        if level == 1:
                            connection.execute(
                                "INSERT INTO metadata (key, value) VALUES (?, ?)",
                                (f"nan_band_{band}", str(not has_non_nan_pixels)),
                            )
                            connection.execute(
                                "INSERT INTO metadata (key, value) VALUES (?, ?)",
                                (f"finite_band_{band}", str(has_finite_pixels)),
                            )

                    previous_rows, previous_cols = out_rows, out_cols

            os.replace(temp_path, path)
        finally:
            temp_path.unlink(missing_ok=True)

    @staticmethod
    def _read_region(
        connection: sqlite3.Connection,
        band: int,
        level: int,
        row_start: int,
        row_stop: int,
        col_start: int,
        col_stop: int,
        level_rows: int,
        level_cols: int,
        tile_size: int,
        dtype: np.dtype,
    ) -> np.ndarray:
        row_start = max(0, row_start)
        col_start = max(0, col_start)
        row_stop = min(level_rows, row_stop)
        col_stop = min(level_cols, col_stop)
        region = np.empty((row_stop - row_start, col_stop - col_start), dtype=dtype)
        first_tile_row = row_start // tile_size
        last_tile_row = (row_stop - 1) // tile_size
        first_tile_col = col_start // tile_size
        last_tile_col = (col_stop - 1) // tile_size
        for tile_row in range(first_tile_row, last_tile_row + 1):
            for tile_col in range(first_tile_col, last_tile_col + 1):
                blob = connection.execute(
                    """
                    SELECT data FROM tiles
                    WHERE level = ? AND band = ? AND tile_row = ? AND tile_col = ?
                    """,
                    (level, band, tile_row, tile_col),
                ).fetchone()
                if blob is None:
                    raise ValueError(
                        f"Missing tile in image pyramid: level {level}, "
                        f"band {band}, tile ({tile_row}, {tile_col})"
                    )

                tile_y = tile_row * tile_size
                tile_x = tile_col * tile_size
                tile_height = min(tile_size, level_rows - tile_y)
                tile_width = min(tile_size, level_cols - tile_x)
                tile = np.frombuffer(zlib.decompress(blob[0]), dtype=dtype).reshape(
                    tile_height, tile_width
                )
                y0 = max(row_start, tile_y)
                y1 = min(row_stop, tile_y + tile_height)
                x0 = max(col_start, tile_x)
                x1 = min(col_stop, tile_x + tile_width)
                region[
                    y0 - row_start : y1 - row_start, x0 - col_start : x1 - col_start
                ] = tile[y0 - tile_y : y1 - tile_y, x0 - tile_x : x1 - tile_x]
        return region

    def level_dimensions(self, level: int) -> tuple[int, int]:
        if not 0 <= level <= self.max_level:
            raise ValueError(f"Invalid image pyramid level: {level}")
        factor = 2**level
        return math.ceil(self.rows / factor), math.ceil(self.cols / factor)

    def read_region(
        self,
        band: int,
        level: int,
        row_start: int,
        row_stop: int,
        col_start: int,
        col_stop: int,
    ) -> np.ndarray:
        level_rows, level_cols = self.level_dimensions(level)
        if not 0 <= band < self.bands:
            raise ValueError(f"Invalid image band: {band}")
        if level == 0:
            raise ValueError("Full-resolution pixels are read from the source image.")
        with closing(sqlite3.connect(self.path)) as connection:
            dtype_row = connection.execute(
                "SELECT value FROM metadata WHERE key = ?",
                (f"dtype_{level}",),
            ).fetchone()
            if dtype_row is None:
                raise ValueError(f"Missing dtype metadata for pyramid level {level}")
            return self._read_region(
                connection,
                band,
                level,
                row_start,
                row_stop,
                col_start,
                col_stop,
                level_rows,
                level_cols,
                self.tile_size,
                np.dtype(dtype_row[0]),
            )

    def find_nan_bands(self, image_data: ImageData) -> np.ndarray:
        level = self.max_level
        if level == 0:
            rows, cols = self.level_dimensions(level)
            return np.array(
                [
                    np.isnan(image_data.read_window(band, 0, rows, 0, cols)).all()
                    for band in range(self.bands)
                ],
                dtype=bool,
            )
        with closing(sqlite3.connect(self.path)) as connection:
            metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        return np.array(
            [metadata[f"nan_band_{band}"] == "True" for band in range(self.bands)],
            dtype=bool,
        )

    def has_finite_data(self, image_data: ImageData) -> bool:
        if self.max_level == 0:
            return any(
                np.isfinite(
                    image_data.read_window(band, 0, self.rows, 0, self.cols)
                ).any()
                for band in range(self.bands)
            )
        with closing(sqlite3.connect(self.path)) as connection:
            metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        return any(
            metadata[f"finite_band_{band}"] == "True" for band in range(self.bands)
        )
