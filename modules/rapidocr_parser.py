from pathlib import Path

from rapidocr_onnxruntime import RapidOCR
from modules.ocr_cache import (
    load_cache,
    save_cache,
)
from modules.image_filter import should_process

from modules.smolvlm_caption import (
    image_hash,
    find_similar_hash,
)


def extract_ocr_text(assets_dir):
    """
    Extract OCR text from all images inside assets folder.

    Parameters
    ----------
    assets_dir : str | Path

    Returns
    -------
    dict

    {
        "image_1.png":
        {
            "text": "...",
            "char_count": 120,
            "line_count": 8
        },

        ...
    }
    """

    assets_dir = Path(assets_dir)

    ocr_engine = RapidOCR()
    cache = load_cache()

    cache_hits = 0
    ocr_skipped = 0
    results = {}

    image_files = sorted(
        [
            *assets_dir.glob("*.png"),
            *assets_dir.glob("*.jpg"),
            *assets_dir.glob("*.jpeg"),
            *assets_dir.glob("*.webp"),
        ]
    )

    for image_path in image_files:

        # ---------------------------------------
        # Image Filter
        # ---------------------------------------

        if not should_process(image_path):

            ocr_skipped += 1

            continue


        # ---------------------------------------
        # pHash Cache
        # ---------------------------------------

        current_hash = image_hash(image_path)

        similar_hash = find_similar_hash(
            current_hash,
            cache
        )

        if similar_hash is not None:

            results[image_path.name] = cache[similar_hash]

            cache_hits += 1

            print(f"Using cached OCR for {image_path.name}")

            continue

        ocr_result, _ = ocr_engine(
            str(image_path)
        )

        extracted_text = ""

        if ocr_result:

            extracted_text = "\n".join(

                line[1]

                for line in ocr_result

            )

        results[image_path.name] = {

            "text": extracted_text,

            "char_count": len(
                extracted_text.strip()
            ),

            "line_count": len(
                extracted_text.splitlines()
            )

        }

        cache[str(current_hash)] = results[image_path.name]

    # ---------------------------------------
    # Count images that contain OCR text
    # ---------------------------------------

    ocr_image_count = sum(
        1
        for item in results.values()
        if item["char_count"] > 0
    )
    save_cache(cache)
    return {

        "results": results,

        "ocr_image_count": ocr_image_count,

        "cache_hits": cache_hits,

        "skipped": ocr_skipped,
    }