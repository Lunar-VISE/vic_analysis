import numpy as np
from shapely import Point, Polygon

from vic_analysis.geometry.bounding_box import BoundingBoxModel


def _get_vertices_bounding_box(vertices: np.ndarray) -> BoundingBoxModel:
    bottom_left = (vertices[:, 0].min(), vertices[:, 1].max())
    top_right = (vertices[:, 0].max(), vertices[:, 1].min())
    return BoundingBoxModel.from_extent(bottom_left, top_right)


def find_pixels_in_polygon(vertices: np.ndarray) -> np.ndarray:
    poly = Polygon(vertices[:, ::-1])
    bbox = _get_vertices_bounding_box(vertices)
    indexer = (slice(bbox.top, bbox.bottom), slice(bbox.left, bbox.right))

    ypixels, xpixels = np.mgrid[*indexer]
    in_pixels: list[tuple[int, int]] = []
    for x, y in zip(ypixels.flatten(), xpixels.flatten()):
        if poly.contains(Point(x, y)):
            in_pixels.append((int(x), int(y)))

    return np.asarray(in_pixels)


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPoly

    verts = np.array([[0, 0], [1, 0], [1.5, 0.4], [0.8, 0.6], [0.15, 0.2]])
    verts *= 10

    in_pixels, shapely_poly = find_pixels_in_polygon(verts)
    print(in_pixels)

    image = np.zeros((20, 20))
    image[in_pixels[:, 1], in_pixels[:, 0]] = 1
    f, ax = plt.subplots()
    ax.imshow(image)
    ax.scatter(verts[:, 1], verts[:, 0])
    ax.add_artist(MplPoly(verts[:, ::-1], facecolor=(0, 0, 0, 0), edgecolor="k"))
    plt.show()
