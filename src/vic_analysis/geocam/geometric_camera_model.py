from dataclasses import dataclass

import numpy as np


@dataclass
class IntrinsicParameters:
    """
    Intrinsic parameters of a camera.

    Parameters
    ----------
    focal_length : float
        Focal length of the camera in meters.
    center_pixel : tuple[int, int]
        Coordinates of the center pixel in the image.
    pixel_pitch : float
        Pitch of the pixels in meters.
    pixel_height : int
        Height of the imaging array in pixels.
    pixel_width : int
        Width of the imaging array in pixels.
    """

    focal_length: float
    pixel_pitch: float
    pixel_height: int
    pixel_width: int
    center_pixel: tuple[int, int] | None = None

    @property
    def center_point(self) -> tuple[float, float]:
        """
        Center of the imaging array in m.
        """
        if self.center_pixel is not None:
            center_x = self.pixel_pitch * self.center_pixel[0]
            center_y = self.pixel_pitch * self.center_pixel[1]
        else:
            center_y = self.pixel_pitch * self.pixel_height / 2
            center_x = self.pixel_pitch * self.pixel_width / 2
        return (center_x, center_y)

    @property
    def matrix(self) -> np.ndarray:
        mat = np.zeros((3, 4))
        mat[[0, 1], [0, 1]] = self.focal_length
        mat[0:2, 2] = self.center_point
        mat[2, 2] = 1
        return mat


if __name__ == "__main__":
    from vic_analysis.detector_specs import DETECTOR_SIZE

    intri = IntrinsicParameters(
        focal_length=12.55e-3,
        pixel_pitch=2.2e-6,
        pixel_height=DETECTOR_SIZE[1],
        pixel_width=DETECTOR_SIZE[0],
    )

    print(np.linalg.inv(intri.matrix))
