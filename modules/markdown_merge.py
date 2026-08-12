from pathlib import Path


def merge_markdown(
    markdown_path,
    assets_dir,
    ocr_results,
    captions,
    output_path=None,
):
    """
    Merge Docling Markdown with:
    - image references
    - image captions
    - OCR text

    Parameters
    ----------
    markdown_path : str | Path

    assets_dir : str | Path

    ocr_results : dict

    captions : dict

    output_path : str | Path | None

    Returns
    -------
    Path
    """

    markdown_path = Path(markdown_path)
    assets_dir = Path(assets_dir)

    if output_path is None:
        output_path = markdown_path
    else:
        output_path = Path(output_path)

    markdown = markdown_path.read_text(
        encoding="utf-8"
    )

    image_files = sorted(
    [
        *assets_dir.glob("*.png"),
        *assets_dir.glob("*.jpg"),
        *assets_dir.glob("*.jpeg"),
        *assets_dir.glob("*.webp"),
    ]
)
    # print("\n===== Images seen by merge =====")

    # for image in image_files:
    #     print(image.name)

    # print("===============================\n")
    

    figure_number = 1

    for image_path in image_files:

        if "<!-- image -->" not in markdown:
            break

        image_name = image_path.name

        caption = captions.get(image_name, "").strip()

        ocr = ocr_results.get(
            image_name,
            {
                "text": ""
            }
        )

        ocr_text = ocr["text"].strip()

        # Skip images with no useful information
        if not caption and not ocr_text:

            markdown = markdown.replace(
                "<!-- image -->",
                "",
                1
            )

            continue

        replacement = []

        replacement.append(f"### Figure {figure_number}")
        replacement.append("")

        replacement.append(
            f"![{image_name}](../temp_assets/{image_name})"
        )
        if caption:

            replacement.append("")
            replacement.append("> **Image Description**")
            replacement.append(">")
            replacement.append(f"> {caption}")

        if ocr_text:

            replacement.append("")
            replacement.append("> **OCR Extract**")
            replacement.append(">")

            for line in ocr_text.splitlines():
                replacement.append(f"> {line}")

        replacement.append("")

    #     print(
    #     f"Merging image: {image_name}"
    # )
        
        markdown = markdown.replace(
            "<!-- image -->",
            "\n".join(replacement),
            1
        )

        figure_number += 1

    output_path.write_text(
        markdown,
        encoding="utf-8"
    )

    return output_path