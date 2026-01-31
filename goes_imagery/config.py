"""Configuration and constants for GOES imagery processing."""

from dataclasses import dataclass


@dataclass
class SatelliteConfig:
    """Configuration for a GOES satellite."""
    name: str
    bucket: str
    longitude: float  # degrees (negative = West)
    description: str


# Available GOES satellites
SATELLITES = {
    "goes-east": SatelliteConfig(
        name="GOES-19",
        bucket="noaa-goes19",
        longitude=-75.2,
        description="GOES-East (Atlantic, Americas East Coast)",
    ),
    "goes-west": SatelliteConfig(
        name="GOES-18",
        bucket="noaa-goes18",
        longitude=-137.2,
        description="GOES-West (Pacific, Americas West Coast)",
    ),
    "goes-16": SatelliteConfig(
        name="GOES-16",
        bucket="noaa-goes16",
        longitude=-75.2,
        description="GOES-16 (former GOES-East, standby)",
    ),
    "goes-17": SatelliteConfig(
        name="GOES-17",
        bucket="noaa-goes17",
        longitude=-137.2,
        description="GOES-17 (former GOES-West, decommissioned)",
    ),
    "goes-18": SatelliteConfig(
        name="GOES-18",
        bucket="noaa-goes18",
        longitude=-137.2,
        description="GOES-18 (alias for goes-west)",
    ),
    "goes-19": SatelliteConfig(
        name="GOES-19",
        bucket="noaa-goes19",
        longitude=-75.2,
        description="GOES-19 (alias for goes-east)",
    ),
}

DEFAULT_SATELLITE = "goes-west"

# Cloud and Moisture Imagery Product - Full Disk
PRODUCT = "ABI-L2-CMIPF"

# Band definitions for true color RGB
# Band 1: Blue (0.47 μm) - 1km resolution
# Band 2: Red (0.64 μm) - 0.5km resolution  
# Band 3: Veggie/Near-IR (0.86 μm) - 1km resolution (used for synthetic green)
RGB_BANDS = [1, 2, 3]

# CIMSS formula for synthetic green channel
# Green = 0.45*Red + 0.10*Veggie + 0.45*Blue
GREEN_COEFFICIENTS = (0.45, 0.10, 0.45)  # (red, veggie, blue)

# Default processing parameters
DEFAULT_EARTH_SIZE = 2048  # Pixels for Earth diameter
DEFAULT_PADDING_RATIO = 2.1  # Final image size = earth_size * padding_ratio
DEFAULT_GAMMA = 2.2  # Gamma correction for better visualization
