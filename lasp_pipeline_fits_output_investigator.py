from pathlib import Path

import matplotlib.pyplot as plt
from astropy.io import fits


def view_lasp_fits(fp: Path | str):
    # view_cube = np.
    with fits.open(fp) as hdul:
        nimgs = len(hdul)

    print(nimgs)


if __name__ == "__main__":
    view_lasp_fits(
        "D:/panorama_testing/vic_pano2_100626_90degrees/lvise_vic_l0_20261006t191403_v000.fits"
    )
