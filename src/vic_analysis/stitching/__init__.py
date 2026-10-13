"""
`stitching`
---
Stitching and Referencing Routines for LV-VIC


Stitching Modules
---
- `picket_fence` // Naive stitching of VIC images that aligns them on the long
edge given some overlap between images and some overlap between bands.
- `geometric` // Stitches images informed by the VIC geometric camera model
defined in `vic_model.py`. See module for more details.

Utility Modules
---
- `vic_model` // Defines the VIC geometric camera model.
- `detector_model` // Defines a dataclass model for the VIC detector plate.
- `spatial_utilities` // Various utilities related to spatial interpretation.
"""
