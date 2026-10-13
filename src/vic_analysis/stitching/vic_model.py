import numpy as np
from cameratransform import SpatialOrientation
from cameratransform.camera import Camera, RectilinearProjection
from scipy.interpolate import LinearNDInterpolator

from src.vic_analysis.stitching.detector_model import (
    VIC_WHOLE_FRAME,
)

from .detector_model import DetectorRegion
from .spatial_utilities import ExtentPolygon, GeometricImage


class LVVIC(Camera):
    """
    LV-VIC
    ------
    Geometric camera model for the Lunar-VISE Visible Infrared Camera (LV-VIC)

    Attributes
    ----------
    center_x: float
        The x-coordinate of the image center in pixels.
    center_y: float
        The y-coordinate of the image center in pixels.
    focal_length_px: float
        The focal length of the camera in pixels.
    sensor_height_m: float
        The height of the camera sensor in meters.
    sensor_width_m: float
        The width of the camera sensor in meters.
    """

    focal_length_m: float = 12.65e-3  # m
    pixel_pitch_m: float = 2.2e-6  # m
    image_height: int = 2004  # pixels
    image_width: int = 2752  # pixels
    center_y: int = 1159  # pixels
    center_x: int = 999  # pixels
    pupil_offset_x = 76e-3  # m
    pupil_offset_y = 0  # m
    pupil_offset_z = -122e-3  # m

    def __init__(self):
        default_orientation = SpatialOrientation(
            elevation_m=0,
            tilt_deg=0,
            roll_deg=0,
            heading_deg=0,
        )
        super().__init__(projection=self._prj, orientation=default_orientation)

    @property
    def focal_length_px(self) -> float:
        return self.focal_length_m / self.pixel_pitch_m

    @property
    def sensor_height_m(self) -> float:
        return self.image_height * self.pixel_pitch_m

    @property
    def sensor_width_m(self) -> float:
        return self.image_width * self.pixel_pitch_m

    @property
    def _prj(self) -> RectilinearProjection:
        return RectilinearProjection(
            focallength_mm=self.focal_length_m * 10**3,
            center_x_px=self.center_x,
            center_y_px=self.center_y,
            image_width_px=self.image_width,
            image_height_px=self.image_height,
            sensor_width_mm=self.sensor_width_m * 10**3,
            sensor_height_mm=self.sensor_height_m * 10**3,
        )

    def get_flat_image_extent(
        self, region: DetectorRegion, z: int, **kwargs
    ) -> ExtentPolygon:
        return ExtentPolygon(
            np.asarray(self.spaceFromImage(region.corners, Z=z))[:, :2],
            **kwargs,
        )

    def image_to_space(self, image: GeometricImage, z: int) -> np.ndarray:
        return np.asarray(self.spaceFromImage(image.pixel_coords, Z=z))


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from scipy.spatial import KDTree
    from skimage.data import coffee

    img = coffee()
    geoimg = GeometricImage.from_image(img[:, :, 0], 0, 0)
    region = DetectorRegion(0, geoimg.height, geoimg.width, 0)

    vic = LVVIC()

    f, ax = plt.subplots()
    ax.set_aspect("equal")
    z = -8
    image_distances = np.empty(len(range(40, 41, 1)))
    image_coords: list[np.ndarray] = []
    image_vals: list[np.ndarray] = []
    image_extents: list[ExtentPolygon] = []
    for n, i in enumerate(range(40, 41, 1)):
        vic.tilt_deg = i
        camera_view = vic.image_to_space(geoimg, z)
        cam_tree = KDTree(camera_view)
        distances, indices = cam_tree.query(camera_view, k=[2])
        median_distance = np.median(distances)
        image_distances[n] = median_distance
        poly = vic.get_flat_image_extent(VIC_WHOLE_FRAME, z, fc=(0, 0, 0, 0), ec="k")
        image_coords.append(camera_view[:, :2])
        image_vals.append(geoimg.values)
        image_extents.append(poly)

    UNDERSAMPLE_FACTOR = 1
    grid_spacing = np.median(image_distances) * UNDERSAMPLE_FACTOR
    image_grid_top = max([i[:, 1].max() for i in image_coords])
    image_grid_bottom = min([i[:, 1].min() for i in image_coords])
    image_grid_right = max([i[:, 0].max() for i in image_coords])
    image_grid_left = min([i[:, 0].min() for i in image_coords])
    y_coords = np.arange(image_grid_bottom, image_grid_top, grid_spacing)
    x_coords = np.arange(image_grid_left, image_grid_right, grid_spacing)
    image_grid_x, image_grid_y = np.meshgrid(x_coords, y_coords)
    grid_coords = np.column_stack([image_grid_x.ravel(), image_grid_y.ravel()])

    image_coords_flattened = np.concat(image_coords, axis=0)
    image_values_flattened = np.concat(image_vals)

    # print(grid_coords[0, :])
    # print(image_coords_flattened[0, :])

    rng = np.random.default_rng()
    idx = rng.integers(0, image_coords_flattened.shape[0], 2000)
    idx2 = rng.integers(0, grid_coords.shape[0], 2000)
    ax.scatter(
        image_coords_flattened[idx, 0], image_coords_flattened[idx, 1], s=0.1, color="k"
    )
    for i in image_extents:
        ax.add_patch(i)
        ax.relim()
        ax.autoscale_view()
    plt.scatter(grid_coords[idx2, 0], grid_coords[idx2, 1], s=0.1, color="r")

    # print(grid_coords.max(axis=0), grid_coords.min(axis=0))
    # print(image_coords_flattened.max(axis=0), image_coords_flattened.min(axis=0))
    # print(image_coords_flattened.shape, image_values_flattened.shape)
    interp = LinearNDInterpolator(image_coords_flattened, image_values_flattened)
    # print(interp(grid_coords[0, :]))
    final_image = interp(grid_coords).reshape(image_grid_x.shape)[::-1, :]

    plt.figure()
    plt.imshow(final_image, cmap="Greys_r")
    plt.show()

    # print(extent_m)
