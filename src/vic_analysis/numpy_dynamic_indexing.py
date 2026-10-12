import numpy as np

type Index = slice | int | list[int]
type Indexer = list[slice | int | list[int]]


def get_flat_indices(index: tuple[slice, slice], shape: tuple[int, int]) -> np.ndarray:
    return np.ravel_multi_index(np.ogrid[*index], shape).ravel()


def slice_along(
    arr: np.ndarray, index: Index | tuple[Index, ...], axis: int | tuple[int, ...]
) -> np.ndarray:
    """
    Dynamically slices array using (an) index value(s) along (an) axis(es).

    Parameters
    ----------
    arr: np.ndarray
        Array to be sliced
    index: slice | int | tuple[slice | int, ...]
        Index or set of indices used as slicing parameters
    axis: int | tuple[int, ...]
        Axis or axes to apply slicing along. If it is a tuple, must be the same
        length as `index`

    Returns
    -------
    np.ndarray
        Sliced array.
    """
    axes = (axis,) if isinstance(axis, int) else axis
    indices = (index,) if isinstance(index, (int, slice)) else index

    if len(axes) != len(indices):
        raise ValueError("The number of indices does not match the number of axes.")

    if len(set(axes)) != len(axes):
        raise ValueError("Each axis may only be specified once.")

    indexer: Indexer = [slice(None)] * arr.ndim

    for axis_, index_ in zip(axes, indices):
        if not -arr.ndim <= axis_ < arr.ndim:
            raise np.exceptions.AxisError(axis_, arr.ndim)

        indexer[axis_] = index_

    return arr[tuple(indexer)]


if __name__ == "__main__":
    from vic_analysis.read.cube_format import CubeFormat

    arr = np.ones((35, 250, 100))
    fmt = CubeFormat.BRC

    sliced = slice_along(arr, slice(3, 27), fmt.band_axis)
    print(arr.shape, sliced.shape)
