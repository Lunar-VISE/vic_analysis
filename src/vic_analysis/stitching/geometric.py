"""
Geometric Stitching
---
Stitches VIC images using a geometric camera model. The pipeline is as follows:

**INGESTION >> RAY-TRACING >> UNIFORM GRIDDING >> CUBE STACKING**

    1. **Image Ingestion:** Takes a dense 2D numpy array representing an image and
    turns it into a `GeometricImage` object. Also, attaches a DetectorRegion
    to this image to locate the set of pixels within the context of the full
    VIC detector plate.

    2. **Ray-Tracing:** Uses the `cameratransform` package to ray trace
    image pixels into the real world. By default, it uses a flat 2D plane at a
    set distance, but a 3D mesh can be used to improve accuracy.

        2a. If the image is projected into 3D space, this data is then projected
        onto a 2D plane for viewing.

    3. **Uniform Gridding:** The result of ray-tracing provides a non-uniform
    point cloud. Using a KDTree from `scipy`, a uniform grid spacing is found
    for a set of projected VIC images. The uniform grid is then filled in using
    linear interpolation (or nearest neighbor to save time).

    4. **Cube Stacking:** Once all bands have been stitched to the same uniform
    grid, a spectral cube can be made by stacking individual bands.
"""

import numpy as np
import numpy.typing as npt

from vic_analysis.detector_specs import BandName
from vic_analysis.stitching.detector_model import VIC_DETECTOR
from vic_analysis.stitching.spatial_utilities import GeometricImage


def vic_image_to_geometric(
    image_array: npt.NDArray[np.float32],
    starting_column: int | None = None,
    filter_name: BandName | None = None,
) -> GeometricImage:
    if all(i is None for i in [starting_column, filter_name]):
        raise TypeError("One of {starting_column, filter_name} must be supplied.")

    if starting_column is not None:
        return GeometricImage.from_image(
            image_array, topmost_pixel=0, leftmost_pixel=starting_column
        )
    elif filter_name is not None:
        left_pixel = VIC_DETECTOR.get_region(filter_name).left
        return GeometricImage.from_image(
            image_array, topmost_pixel=0, leftmost_pixel=left_pixel
        )
    else:
        raise ValueError("This error will not occur.")


if __name__ == "__main__":
    from vic_analysis.read.lv_pipeline import read_l0_pipeline_file

    data = read_l0_pipeline_file(
        "D:/panorama_testing/vic_pano2_100626_90degrees/lvise_vic_l0_20261006t191403_v000.fits"
    )

    # for n, i in enumerate(data.metadata):
    #     print(data.image.array[:, :, n].shape, i.band_id, i.image_id)
