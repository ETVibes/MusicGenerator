"""===============================================================================
Module: config.py
Description: Centralized path configuration used across the entire project.
==============================================================================="""

from pathlib import Path

# Automatically determine the project root directory (adjust .parents count if needed)
# If config.py is inside `src/`, root is one level up (.parents[1]). 
# If config.py is in the root folder, use Path(__file__).resolve().parent
ROOT_DIR = Path(__file__).resolve().parent.parent

# Define all core directories here in one place
OUTPUT_DIR = ROOT_DIR / "output"
SINGLE_IMAGE_DIR = OUTPUT_DIR / "Single_Image"
CAROUSEL_DIR = OUTPUT_DIR / "Carousel_Posts"
CAROUSEL_CURRENT_DIR = CAROUSEL_DIR / "current"
REEL_DIR = OUTPUT_DIR / "Reels"
ASSETS_DIR = ROOT_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "Font"

# Ensure essential output directories exist automatically upon import
for path in [SINGLE_IMAGE_DIR, CAROUSEL_CURRENT_DIR, REEL_DIR]:
    path.mkdir(parents=True, exist_ok=True)