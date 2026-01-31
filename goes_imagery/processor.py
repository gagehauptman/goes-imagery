"""Process GOES band data into true-color RGB imagery."""

import numpy as np
from PIL import Image

from .config import DEFAULT_GAMMA, GREEN_COEFFICIENTS


def normalize_band(data: np.ndarray, gamma: float = DEFAULT_GAMMA) -> np.ndarray:
    """
    Normalize band data to 0-255 with gamma correction.
    NaN values become 0 (black for space).
    
    Args:
        data: 2D array of reflectance values (0-1 range, NaN for invalid).
        gamma: Gamma correction value.
    
    Returns:
        2D uint8 array (0-255).
    """
    result = np.zeros(data.shape, dtype=np.float32)
    valid = ~np.isnan(data)
    
    # Clip to valid reflectance range
    clipped = np.clip(data[valid], 0, 1)
    
    # Normalize and apply gamma correction
    result[valid] = np.power(clipped, 1 / gamma)
    
    return (result * 255).astype(np.uint8)


def create_true_color(
    red: np.ndarray,
    veggie: np.ndarray,
    blue: np.ndarray,
    gamma: float = DEFAULT_GAMMA,
) -> np.ndarray:
    """
    Create true-color RGB image from GOES bands.
    
    Uses CIMSS formula for synthetic green channel since GOES lacks a true green band.
    
    Args:
        red: Band 2 data (red channel).
        veggie: Band 3 data (near-IR, used for green synthesis).
        blue: Band 1 data (blue channel).
        gamma: Gamma correction value.
    
    Returns:
        3D uint8 array (H, W, 3) in RGB format.
    """
    # Ensure all bands are same size
    size = min(red.shape[0], veggie.shape[0], blue.shape[0])
    red = red[:size, :size]
    veggie = veggie[:size, :size]
    blue = blue[:size, :size]
    
    # Create combined space mask
    space_mask = np.isnan(red) | np.isnan(veggie) | np.isnan(blue)
    
    # Normalize bands
    red_norm = normalize_band(red, gamma)
    veggie_norm = normalize_band(veggie, gamma)
    blue_norm = normalize_band(blue, gamma)
    
    # Compute synthetic green using CIMSS formula
    r_coef, v_coef, b_coef = GREEN_COEFFICIENTS
    green_norm = (
        r_coef * red_norm.astype(np.float32)
        + v_coef * veggie_norm.astype(np.float32)
        + b_coef * blue_norm.astype(np.float32)
    ).astype(np.uint8)
    
    # Force space to black in all channels
    red_norm[space_mask] = 0
    green_norm[space_mask] = 0
    blue_norm[space_mask] = 0
    
    return np.stack([red_norm, green_norm, blue_norm], axis=2)


def add_padding(rgb: np.ndarray, padding_ratio: float) -> np.ndarray:
    """
    Add black padding around Earth to show it floating in space.
    
    Args:
        rgb: 3D array (H, W, 3) of Earth imagery.
        padding_ratio: Ratio of final size to Earth size.
                       e.g., 2.0 means Earth takes up half the image.
    
    Returns:
        Padded 3D array.
    """
    h, w = rgb.shape[:2]
    new_size = int(max(h, w) * padding_ratio)
    
    # Create black canvas
    padded = np.zeros((new_size, new_size, 3), dtype=np.uint8)
    
    # Center Earth
    offset_y = (new_size - h) // 2
    offset_x = (new_size - w) // 2
    padded[offset_y : offset_y + h, offset_x : offset_x + w] = rgb
    
    return padded


def render_image(
    red: np.ndarray,
    veggie: np.ndarray,
    blue: np.ndarray,
    padding_ratio: float = 1.0,
    gamma: float = DEFAULT_GAMMA,
) -> Image.Image:
    """
    Render final Earth image from band data.
    
    Args:
        red, veggie, blue: Band data arrays.
        padding_ratio: Space padding (1.0 = no padding, 2.0 = Earth is half the image).
        gamma: Gamma correction.
    
    Returns:
        PIL Image object.
    """
    rgb = create_true_color(red, veggie, blue, gamma)
    
    if padding_ratio > 1.0:
        rgb = add_padding(rgb, padding_ratio)
    
    return Image.fromarray(rgb)
