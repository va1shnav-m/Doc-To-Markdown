from pathlib import Path
from PIL import Image


MIN_WIDTH = 180
MIN_HEIGHT = 180

MIN_OCR_CHARACTERS = 15


def should_caption(image_path):
    """
    Decide whether an image should be sent to SmolVLM.

    Returns
    -------
    bool
    """

    image_path = Path(image_path)

    img = Image.open(image_path)

    width, height = img.size

    # ---------------------------------------------------
    # Rule 1
    # Skip only if BOTH dimensions are very small
    # ---------------------------------------------------

    if width < MIN_WIDTH and height < MIN_HEIGHT:

        print(f"{image_path.name}: Tiny image -> Skip")

        return False

   

    # ---------------------------------------------------
    # Otherwise
    # ---------------------------------------------------

    print(f"{image_path.name}: Send to SmolVLM")

    return True