# GOES Imagery

Generate true-color RGB imagery from GOES geostationary weather satellites.

Fetches raw band data from NOAA's AWS bucket and composites it into a proper RGB image with Earth floating in space.

## Features

- **Multiple satellites** - GOES-East (Atlantic) and GOES-West (Pacific)
- **True RGB** from raw visible-light bands (no infrared substitution)
- **Full disc view** with configurable padding (Earth floating in space)
- **Historical data** - access imagery from 2023 to present
- **10-minute intervals** - GOES captures full disc every 10 minutes

## Installation

```bash
cd /storage/git/goes-imagery
pip install -e .
```

Or with a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# Latest image from GOES-West (default)
goes-imagery -o earth.png

# GOES-East (Atlantic view)
goes-imagery --sat goes-east -o earth.png

# 12 hours ago (daytime if currently night)
goes-imagery -t -12h -o earth.png

# Specific date/time (UTC)
goes-imagery -t "2024-06-15 18:00" -o earth.png

# Higher resolution Earth
goes-imagery -s 4096 -o earth.png

# More zoomed out (more space around Earth)
goes-imagery -p 2.5 -o earth.png

# Just Earth, no padding
goes-imagery -p 1.0 -o earth.png

# Verbose output
goes-imagery -v -o earth.png
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `-o, --output` | Output image path (required) | - |
| `--satellite, --sat` | Satellite to use (see below) | `goes-west` |
| `-t, --time` | Image time (see below) | `now` |
| `-s, --earth-size` | Earth diameter in pixels | 2048 |
| `-p, --padding` | Padding ratio (final = earth × padding) | 2.1 |
| `-g, --gamma` | Gamma correction | 2.2 |
| `-v, --verbose` | Print progress | false |
| `-q, --quiet` | Suppress output | false |

### Satellites

| ID | Satellite | Position | Coverage |
|----|-----------|----------|----------|
| `goes-west` | GOES-18 | 137.2°W | Pacific, Americas West Coast |
| `goes-east` | GOES-19 | 75.2°W | Atlantic, Americas East Coast |
| `goes-18` | GOES-18 | 137.2°W | Alias for goes-west |
| `goes-19` | GOES-19 | 75.2°W | Alias for goes-east |
| `goes-16` | GOES-16 | 75.2°W | Former GOES-East (standby) |
| `goes-17` | GOES-17 | 137.2°W | Former GOES-West (decommissioned) |

### Time formats

- `now` or `latest` - Most recent image
- `-12h` - 12 hours ago
- `-30m` - 30 minutes ago
- `2024-06-15` - Specific date at noon UTC
- `2024-06-15 18:00` - Specific datetime UTC

## Data Source

Uses NOAA's GOES data hosted on AWS S3:
- **Buckets:** `noaa-goes16`, `noaa-goes17`, `noaa-goes18`, `noaa-goes19`
- **Product:** ABI-L2-CMIPF (Cloud and Moisture Imagery, Full Disk)
- **Bands:** 1 (Blue), 2 (Red), 3 (Veggie/Near-IR for synthetic green)

Data available from 2023 to present, updated every 10 minutes.

## How It Works

1. Fetches raw NetCDF band files from AWS S3
2. Extracts reflectance data and handles fill values (space pixels)
3. Resizes bands to match (Band 2 is 2x resolution of 1 & 3)
4. Computes synthetic green using CIMSS formula: `G = 0.45R + 0.10V + 0.45B`
5. Applies gamma correction for proper brightness
6. Adds black padding to show Earth floating in space

## Notes

- **Nighttime imagery** will be mostly dark (this is real RGB, not infrared)
- Large earth sizes (>4096) may use significant memory during processing
- GOES-West views the Pacific; GOES-East views the Atlantic

## Example Wallpaper Script

```bash
#!/bin/bash
# Update GOES wallpaper every 10 minutes

OUTPUT="$HOME/.cache/goes-wallpaper.png"
goes-imagery -q -o "$OUTPUT"
swww img "$OUTPUT" --transition-type=fade --transition-duration=2
```

## License

Public domain satellite data from NOAA. Code is MIT licensed.
