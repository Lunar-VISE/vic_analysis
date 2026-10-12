from copy import copy
from dataclasses import dataclass

import numpy as np

from vic_analysis.detector_specs import VIC_FILTER_REGIONS, BandName, band_names
from vic_analysis.radiance_pipeline.data_model import VICDataset, VICHeader
from vic_analysis.radiance_pipeline.pipeline_model import L0FileContents, VICL0File
from vic_analysis.read.cube_format import CubeFormat
from vic_analysis.read.parse_vic_binary import is_valid_band_name

BAND_ID_BY_NAME: dict[BandName, int] = {
    "Filter1": 4,
    "Filter2": 5,
    "Filter3": 6,
    "Filter4": 7,
    "Filter5": 8,
    "Filter6": 9,
    "Filter7": 10,
}
DEFAULT_OVERLAP_COLUMNS = 48
DEFAULT_FILTER_OFFSET = 385


def _validate_image_size(source_list: list[tuple[int, int]]) -> tuple[int, int]:
    if all(i == source_list[0] for i in source_list):
        return source_list[0]
    raise ValueError("Sizes are not uniform.")


@dataclass
class SingleBandExtraction:
    band_id: int
    frames: list[tuple[np.ndarray, VICHeader]]

    def __post_init__(self):
        self._frame_shape = _validate_image_size(
            [(hdr.nrows, hdr.ncols) for _img, hdr in self.frames]
        )

    @property
    def num_frames(self) -> int:
        return len(self.frames)

    @property
    def frame_width(self) -> int:
        return self._frame_shape[1]

    @property
    def frame_height(self) -> int:
        return self._frame_shape[0]


def _ensure_band_id(band_identifier: BandName | int) -> int:
    """Narrows type of band identifier from string or integer to band ID integer."""
    if isinstance(band_identifier, str):
        if not is_valid_band_name(band_identifier):
            raise ValueError(f"Band ID not found: {band_identifier}")
        band_id = BAND_ID_BY_NAME[band_identifier]
    elif isinstance(band_identifier, int):
        if band_identifier not in [v for v in BAND_ID_BY_NAME.values()]:
            raise ValueError(f"Band ID not found: {band_identifier}")
        band_id = band_identifier
    return band_id


def _extract_single_band(
    image_frames: L0FileContents | list[VICDataset], band_identifier: BandName | int
) -> SingleBandExtraction:
    band_id = _ensure_band_id(band_identifier)
    if isinstance(image_frames, L0FileContents):
        iter_copy = copy(image_frames)
        target_frames = [
            (img.data, hdr) for img, hdr in iter_copy if hdr.band_id == band_id
        ]
    elif isinstance(image_frames, list):
        target_frames = [
            (i.data.make_array(), i.header)
            for i in image_frames
            if i.header.band_id == band_id
        ]
    return SingleBandExtraction(band_id, target_frames)


def _execute_stitching(
    target_slices: SingleBandExtraction, overlapping_columns: int
) -> np.ndarray:
    index = 0
    pano = np.full(
        (
            target_slices.frame_height,
            (target_slices.frame_width * target_slices.num_frames),
        ),
        fill_value=np.nan,
    )
    for img_hdu, _hdr in target_slices.frames:
        img = img_hdu.data
        starting_column = max(0, index - overlapping_columns)
        ending_column = starting_column + target_slices.frame_width
        column_slice = slice(starting_column, ending_column)
        img_stack = np.stack([img, pano[:, column_slice]], axis=-1)
        pano[:, column_slice] = np.nanmax(img_stack, axis=-1)
        index = ending_column
    return pano


def stitch_single_band(
    image_slices: L0FileContents | list[VICDataset],
    band_name: BandName,
    overlapping_columns: int = DEFAULT_OVERLAP_COLUMNS,
) -> tuple[np.ndarray, int]:
    target_slices = _extract_single_band(image_slices, band_name)
    pano = _execute_stitching(target_slices, overlapping_columns)
    return pano, target_slices.num_frames


def build_pano_cube(
    image_frames: L0FileContents | list[VICDataset],
    filter_offset: int = DEFAULT_FILTER_OFFSET,
    sort_by_wavelength: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    img, _nsteps = stitch_single_band(image_frames, "Filter1")
    pano_cube = np.full(
        (*img.shape, len(band_names)), dtype=np.float32, fill_value=np.nan
    )
    pano_cube[:, :, 0] = img  # Filter1 already loaded
    wvl_array = np.zeros(len(band_names))
    wvl_array[0] = VIC_FILTER_REGIONS.region_set["Filter1"].info.band_center_wavelength

    for n, b in enumerate(band_names[1:]):
        img, _nsteps = stitch_single_band(image_frames, b)
        starting_column = 0 + (n + 1) * filter_offset
        ending_column = img.shape[1] - starting_column
        pano_cube[:, starting_column:, n + 1] = img[:, :ending_column]

        wvl_value = VIC_FILTER_REGIONS.region_set[b].info.band_center_wavelength
        wvl_array[n + 1] = wvl_value

    if sort_by_wavelength:
        sort_idx = np.argsort(wvl_array)
        pano_cube = pano_cube[:, :, sort_idx]
        wvl_array = wvl_array[sort_idx]

    return pano_cube, wvl_array


if __name__ == "__main__":
    import cubio as cb
    import matplotlib.pyplot as plt
    from astropy.io import fits
    from cmap import Colormap
    from cubio.data.crs_wkt_strings import GeographicCRS
    from cubio.geotools.models.geotransform_model import GeotransformModel

    with VICL0File(
        "D:/panorama_testing/vic_pano2_100626_90degrees/lvise_vic_l0_20261006t191403_v000.fits"
    ) as vic:
        cube, wvl = build_pano_cube(vic)
        cc, cd = cb.cube_from_numpy(
            cube,
            "BIP",
            name="vic_pano2_100626_90degrees_DN",
            crs=GeographicCRS.WGS84,
            gtrans=GeotransformModel.null(),
            measvals=list(wvl),
        )

        cb.write_envi(cc, cd, "BIL", "D:/panorama_testing/vic_pano2_100626_90degrees/")

        cube_fits = CubeFormat.RCB.convert_to(cube, "BRC")
        fits.writeto(
            "D:/panorama_testing/vic_pano2_100626_90degrees/vic_pano2_100626_90degrees_DN.fits",
            cube_fits,
            overwrite=True,
        )

    plt.imshow(cube[:, :, 0], cmap=Colormap("crameri:grayc_r").to_mpl())
    plt.show()
