from pathlib import Path
import re


def merge_document_markdown(
    output_dir,
    output_file="document.md",
):
    """
    Merge all page markdown files into one final markdown.

    Parameters
    ----------
    output_dir : str or Path
        Folder containing page markdown files.

    output_file : str
        Final markdown filename.

    Returns
    -------
    Path
        Path to final markdown.
    """

    output_dir = Path(output_dir)

    markdown_files = sorted(
        output_dir.glob("page-*.md"),
        key=lambda x: [
            int(i)
            for i in re.findall(r"\d+", x.stem)
        ]
    )

    final_markdown = []

    for md_file in markdown_files:

        final_markdown.append(
            md_file.read_text(
                encoding="utf-8"
            )
        )

        final_markdown.append("\n\n")

    final_path = output_dir / output_file

    final_path.write_text(
        "".join(final_markdown),
        encoding="utf-8"
    )

    return final_path