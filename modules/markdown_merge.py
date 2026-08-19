from pathlib import Path


def merge_markdown(
    markdown_path,
    assets_dir,
    image_analysis,
    output_path=None,
):
    """
    Merge Docling Markdown with structured image analysis.

    Parameters
    ----------
    markdown_path : str | Path

    assets_dir : str | Path

    image_analysis : dict
        {
            "image_name.png": {
                "type": "diagram",
                "markdown": "..."
            },
            ...
        }

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

    figure_number = 1

    for image_path in image_files:

        if "<!-- image -->" not in markdown:
            break

        image_name = image_path.name

        analysis = image_analysis.get(image_name)

        replacement = []

        replacement.append(f"### Figure {figure_number}")
        replacement.append("")

        replacement.append(
            f"![{image_name}](../temp_assets/{image_name})"
        )

        replacement.append("")

        # Add text extract if available
        text_extract = (
            analysis.get("text_extract", "").strip()
            if analysis else ""
        )

        if text_extract and text_extract.lower() != "no text content.":
            replacement.append("> **Text Extract:**")
            replacement.append(">")
            for line in text_extract.splitlines():
                replacement.append(f"> {line}")
            replacement.append("")

        # Add description if available
        description = (
            analysis.get("description", "").strip()
            if analysis else ""
        )

        if description:
            replacement.append("> **Description:**")
            replacement.append(">")
            for line in description.splitlines():
                replacement.append(f"> {line}")
            replacement.append("")

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