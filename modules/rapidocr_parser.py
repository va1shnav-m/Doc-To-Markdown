from pathlib import Path

from rapidocr_onnxruntime import RapidOCR


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

    return results