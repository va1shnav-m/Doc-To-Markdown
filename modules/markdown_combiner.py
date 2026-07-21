from pathlib import Path


def combine_markdowns(output_dir):

    output_dir = Path(output_dir)

    markdown_files = sorted(
        output_dir.glob("chunk_*.md")
    )

    combined_markdown = []

    for markdown_file in markdown_files:

        markdown = markdown_file.read_text(
            encoding="utf-8"
        ).strip()

        combined_markdown.append(markdown)
        combined_markdown.append("\n\n")

    final_markdown = output_dir / "document.md"

    final_markdown.write_text(
        "".join(combined_markdown),
        encoding="utf-8"
    )

    return final_markdown