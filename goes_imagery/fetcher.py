"""Fetch GOES data from AWS S3."""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3
import netCDF4 as nc
import numpy as np
from botocore import UNSIGNED
from botocore.config import Config
from PIL import Image

from .config import DEFAULT_SATELLITE, PRODUCT, RGB_BANDS, SATELLITES


def get_s3_client():
    """Create anonymous S3 client for public NOAA bucket."""
    return boto3.client("s3", config=Config(signature_version=UNSIGNED))


def find_band_files(
    s3_client,
    target_time: datetime | None = None,
    bands: list[int] = RGB_BANDS,
    satellite: str = DEFAULT_SATELLITE,
) -> dict[int, str]:
    """
    Find the most recent files for specified bands near target_time.
    
    Args:
        s3_client: boto3 S3 client
        target_time: Target datetime (UTC). None = latest available.
        bands: List of band numbers to fetch.
        satellite: Satellite identifier (e.g., 'goes-west', 'goes-east').
    
    Returns:
        Dict mapping band number to S3 key.
    """
    sat_config = SATELLITES[satellite]
    bucket = sat_config.bucket
    
    if target_time is None:
        target_time = datetime.now(timezone.utc)
    elif target_time.tzinfo is None:
        target_time = target_time.replace(tzinfo=timezone.utc)
    
    files = {}
    for band in bands:
        # Search current hour and previous hours
        for hours_back in range(6):
            check_time = target_time - timedelta(hours=hours_back)
            day_of_year = check_time.timetuple().tm_yday
            prefix = f"{PRODUCT}/{check_time.year}/{day_of_year:03d}/{check_time.hour:02d}/"
            
            try:
                response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
                if "Contents" not in response:
                    continue
                
                # Filter for specific band
                band_str = f"M6C{band:02d}"
                band_files = [
                    obj for obj in response["Contents"]
                    if band_str in obj["Key"] and obj["Key"].endswith(".nc")
                ]
                
                if band_files:
                    # Get the most recent one
                    latest = max(band_files, key=lambda x: x["LastModified"])
                    files[band] = (bucket, latest["Key"])
                    break
            except Exception:
                continue
    
    return files


def download_band(s3_client, bucket: str, key: str, target_size: int) -> np.ndarray:
    """
    Download a band file and extract/resize the data.
    
    Args:
        s3_client: boto3 S3 client
        bucket: S3 bucket name
        key: S3 object key
        target_size: Target size to resize to (pixels)
    
    Returns:
        2D numpy array of reflectance values, NaN for invalid/space pixels.
    """
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        s3_client.download_fileobj(bucket, key, tmp)
        tmp_path = Path(tmp.name)
    
    try:
        dataset = nc.Dataset(tmp_path, "r")
        
        # Get CMI (Cloud and Moisture Imagery) variable
        cmi_var = dataset.variables["CMI"]
        data = cmi_var[:]
        fill_value = getattr(cmi_var, "_FillValue", -1)
        dataset.close()
        
        # Create mask for invalid pixels (space)
        if np.ma.is_masked(data):
            mask = data.mask.copy()
            data = data.data
        else:
            mask = (data == fill_value) | (data < 0)
        
        # Convert to float and mark invalid as NaN
        data = data.astype(np.float32)
        data[mask] = np.nan
        
        # Resize using PIL for proper interpolation
        if data.shape[0] != target_size:
            img = Image.fromarray(data)
            img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
            data = np.array(img)
        
        return data
    finally:
        tmp_path.unlink()


def fetch_rgb_bands(
    target_time: datetime | None = None,
    earth_size: int = 2048,
    satellite: str = DEFAULT_SATELLITE,
    verbose: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, datetime]:
    """
    Fetch and process RGB bands from a GOES satellite.
    
    Args:
        target_time: Target datetime (UTC). None = latest.
        earth_size: Size to resize Earth to (pixels).
        satellite: Satellite identifier (e.g., 'goes-west', 'goes-east').
        verbose: Print progress messages.
    
    Returns:
        Tuple of (red, veggie, blue) arrays and actual image timestamp.
    """
    if satellite not in SATELLITES:
        valid = ", ".join(SATELLITES.keys())
        raise ValueError(f"Unknown satellite '{satellite}'. Valid options: {valid}")
    
    sat_config = SATELLITES[satellite]
    s3 = get_s3_client()
    
    if verbose:
        print(f"Satellite: {sat_config.name} ({sat_config.description})")
        print("Finding band files...")
    
    files = find_band_files(s3, target_time, satellite=satellite)
    
    if len(files) < 3:
        raise RuntimeError(f"Could not find all required bands. Found: {list(files.keys())}")
    
    # Extract timestamp from filename (files now contain (bucket, key) tuples)
    bucket, key = files[2]
    filename = key.split("/")[-1]
    ts_str = filename.split("_s")[1].split("_e")[0]
    image_time = datetime.strptime(ts_str, "%Y%j%H%M%S%f").replace(tzinfo=timezone.utc)
    
    if verbose:
        print(f"Image timestamp: {image_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Download bands
    bands_data = {}
    for band_num, (bucket, key) in files.items():
        if verbose:
            print(f"Downloading band {band_num}...")
        bands_data[band_num] = download_band(s3, bucket, key, earth_size)
    
    return bands_data[2], bands_data[3], bands_data[1], image_time  # red, veggie, blue
