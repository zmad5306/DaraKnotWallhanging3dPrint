"""Compatibility import: every build now uses the removable shared carrier.

The old continuous starter-shoe implementation was removed so rebuilding a
production project cannot silently recreate its inaccessible flange.
"""
from veneer_trim_carrier import (
    fin_carrier, slab_xz, rod, line_parts, PITCH, THICKNESS, BACK_GAP,
    TOOTH_PITCH, TOOTH_WIDTH, POCKET_DEPTH,
)
