from pathlib import Path
from PIL import Image

MIN_WIDTH = 180
MIN_HEIGHT = 180

MIN_SIDE = 32              # Skip if one side is extremely small
MAX_ASPECT_RATIO = 15      # Skip very long/thin images

MIN_OCR_CHARACTERS = 15


def should_process(image_path):
    """
    Decide whether an image should be sent to SmolVLM.

    Returns
    -------
    bool
    """

    image_path = Path(image_path)

    with Image.open(image_path) as img:
        width, height = img.size

        # ---------------------------------------------------
        # Rule 1
        # Skip if BOTH dimensions are very small
        # ---------------------------------------------------

        if width < MIN_WIDTH and height < MIN_HEIGHT:
            print(f"{image_path.name}: Tiny image ({width}x{height}) -> Skip")
            return False

        # ---------------------------------------------------
        # Rule 2
        # Skip if one dimension is extremely small
        # (horizontal/vertical lines, borders)
        # ---------------------------------------------------

        if min(width, height) < MIN_SIDE:
            print(f"{image_path.name}: One side too small ({width}x{height}) -> Skip")
            return False

        # ---------------------------------------------------
        # Rule 3
        # Skip extremely long/thin images
        # ---------------------------------------------------

        aspect_ratio = max(width, height) / min(width, height)

        if aspect_ratio > MAX_ASPECT_RATIO:
            print(
                f"{image_path.name}: Extreme aspect ratio "
                f"({width}x{height}, ratio={aspect_ratio:.1f}) -> Skip"
            )
            return False

        # ---------------------------------------------------
        # Rule 4
        # Skip only if EVERY pixel is exactly the same colour
        # ---------------------------------------------------

        colors = img.getcolors(maxcolors=2)

        if colors is not None and len(colors) == 1:
            print(f"{image_path.name}: Solid colour image -> Skip")
            return False

    # ---------------------------------------------------
    # Otherwise
    # ---------------------------------------------------

    print(f"{image_path.name}: Send For Image Processing")

    return True