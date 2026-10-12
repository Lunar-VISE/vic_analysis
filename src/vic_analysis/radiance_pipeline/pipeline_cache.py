"""Small in-memory cache with pluggable persistence.

Implement a Writer for each output format. Each writer owns the on-disk layout;
the cache only owns datasets and delegates saving.

Example:
    cache = CacheModel()
    cache.add(dataset)
    cache.save("radiance.hdf5", HDF5Writer())
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Protocol
from uuid import UUID

import numpy as np

from vic_analysis.radiance_pipeline.data_model import VICDataset


class Writer(Protocol):
    """Interface for a format-specific cache writer."""

    def write(self, cache: CacheModel, path: Path) -> None: ...


class CacheModel:
    """Hold processed datasets and delegate their serialization."""

    def __init__(self) -> None:
        self._datasets: dict[UUID, VICDataset] = {}

    def add_dataset(self, dataset: VICDataset) -> None:
        """Add a dataset, rejecting duplicate (band_id, image_id) keys."""
        if dataset.uuid in self._datasets:
            raise ValueError(f"Dataset already cached: {dataset.uuid}")
        self._datasets[dataset.uuid] = dataset

    def add_metaimage(
        self, parent_dataset_uuid: UUID, data: np.ndarray, name: str
    ) -> None:
        dset = self.get(parent_dataset_uuid)

    def get(self, uuid: UUID) -> VICDataset:
        """Return a dataset by its band and image IDs."""
        return self._datasets[uuid]

    def __iter__(self) -> Iterator[VICDataset]:
        return iter(self._datasets.values())

    def __len__(self) -> int:
        return len(self._datasets)

    def save(self, path: Path | str, writer: Writer) -> None:
        """Save this cache using the supplied format-specific writer."""
        writer.write(self, Path(path))
