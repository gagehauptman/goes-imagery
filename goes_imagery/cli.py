"""Command-line interface for GOES imagery generation."""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import DEFAULT_EARTH_SIZE, DEFAULT_GAMMA, DEFAULT_PADDING_RATIO, DEFAULT_SATELLITE, SATELLITES
from .fetcher import fetch_rgb_bands
from .processor import render_image


def parse_time(time_str: str) -> datetime:
    """
    Parse time string into datetime.
    
    Supports:
        - "now" or "latest": current time
        - "-Nh" or "-Nm": N hours/minutes ago
        - "YYYY-MM-DD": specific date at noon UTC
        - "YYYY-MM-DD HH:MM": specific datetime UTC
        - "YYYY-MM-DDTHH:MM:SS": ISO format
    """
    time_str = time_str.strip().lower()
    
    if time_str in ("now", "latest"):
        return datetime.now(timezone.utc)
    
    # Relative time: -12h, -30m
    if time_str.startswith("-"):
        num = int(time_str[1:-1])
        unit = time_str[-1]
        if unit == "h":
            return datetime.now(timezone.utc) - timedelta(hours=num)
        elif unit == "m":
            return datetime.now(timezone.utc) - timedelta(minutes=num)
        else:
            raise ValueError(f"Unknown time unit: {unit}")
    
    # Absolute time formats
    for fmt in [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]:
        try:
            dt = datetime.strptime(time_str, fmt)
            if fmt == "%Y-%m-%d":
                dt = dt.replace(hour=12)  # Default to noon
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    
    raise ValueError(f"Could not parse time: {time_str}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate true-color RGB imagery from GOES-18 (West) satellite data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Latest image from GOES-West (default)
  goes-imagery -o earth.png

  # GOES-East (Atlantic view)
  goes-imagery --satellite goes-east -o earth.png

  # Image from 12 hours ago
  goes-imagery -t -12h -o earth.png

  # Specific date/time
  goes-imagery -t "2024-06-15 18:00" -o earth.png

  # Higher resolution, more zoom out
  goes-imagery --earth-size 4096 --padding 2.5 -o earth.png

  # Just Earth, no padding
  goes-imagery --padding 1.0 -o earth.png
""",
    )
    
    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Output image path (PNG recommended)",
    )
    
    parser.add_argument(
        "--satellite", "--sat",
        type=str,
        default=DEFAULT_SATELLITE,
        choices=list(SATELLITES.keys()),
        help=f"Satellite to use (default: {DEFAULT_SATELLITE})",
    )
    
    parser.add_argument(
        "-t", "--time",
        type=str,
        default="now",
        help="Image time: 'now', '-12h', '-30m', or 'YYYY-MM-DD HH:MM' (default: now)",
    )
    
    parser.add_argument(
        "-s", "--earth-size",
        type=int,
        default=DEFAULT_EARTH_SIZE,
        help=f"Earth diameter in pixels (default: {DEFAULT_EARTH_SIZE})",
    )
    
    parser.add_argument(
        "-p", "--padding",
        type=float,
        default=DEFAULT_PADDING_RATIO,
        help=f"Padding ratio - final size = earth_size * padding (default: {DEFAULT_PADDING_RATIO})",
    )
    
    parser.add_argument(
        "-g", "--gamma",
        type=float,
        default=DEFAULT_GAMMA,
        help=f"Gamma correction (default: {DEFAULT_GAMMA})",
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress messages",
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors",
    )
    
    args = parser.parse_args()
    
    try:
        target_time = parse_time(args.time)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    verbose = args.verbose and not args.quiet
    
    if verbose:
        print(f"Target time: {target_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Earth size: {args.earth_size}px")
        print(f"Padding ratio: {args.padding}")
    
    try:
        # Fetch bands
        red, veggie, blue, image_time = fetch_rgb_bands(
            target_time=target_time,
            earth_size=args.earth_size,
            satellite=args.satellite,
            verbose=verbose,
        )
        
        if verbose:
            print("Rendering image...")
        
        # Render image
        image = render_image(
            red, veggie, blue,
            padding_ratio=args.padding,
            gamma=args.gamma,
        )
        
        # Save
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image.save(args.output)
        
        if not args.quiet:
            print(f"Saved: {args.output} ({image.size[0]}x{image.size[1]})")
            print(f"Image time: {image_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
