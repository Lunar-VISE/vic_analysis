from pathlib import Path

import cubio as cb
import numpy as np
from cubio.data.crs_wkt_strings import GeographicCRS
from cubio.geotools.models import GeotransformModel

from vic_analysis.detector_specs import VIC_FILTER_REGIONS
from vic_analysis.read.cube_format import CubeFormat


def npz_to_cubio(filepath: Path, name: str, out: Path) -> None:
    wvl = VIC_FILTER_REGIONS.get_wavelengths()
    sort_idx = np.argsort(wvl)
    print(sort_idx)
    cube = np.load(filepath)["cube"]
    print(cube.shape)
    cube = CubeFormat.BRC.convert_to(cube, "RCB")
    cube = cube[::-1, :, sort_idx]  # Flip y-axis and sort spectral bands
    cc, cd = cb.cube_from_numpy(
        cube,
        "BIP",
        name=name,
        crs=GeographicCRS.WGS84,
        gtrans=GeotransformModel.null(),
        measvals=list(wvl[sort_idx]),
    )

    cb.write_envi(cc, cd, "BIL", out)


if __name__ == "__main__":
    npz_to_cubio(
        Path(
            "D:/panorama_testing/vic_pano3_100726_55degrees/geometric_stitching_RDN/cube7.npz"
        ),
        "vic_pano3_RDN",
        Path("D:/panorama_testing/vic_pano3_100726_55degrees/"),
    )
    # import matplotlib.pyplot as plt
    # from cmap import Colormap

    # CLRMAP = Colormap("crameri:grayc_r")
    # cube = np.load("D:/cube_files/pano_10626_45degrees/cube7.npz")["cube"]

    # for n in range(cube.shape[0]):
    #     plt.figure()
    #     plt.imshow(cube[n, ::-1, :], cmap=CLRMAP.to_mpl())

    # plt.show()
