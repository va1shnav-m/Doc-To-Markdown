from pathlib import Path
import fitz


def parse_document(
    input_path,
    output_dir,
    assets_dir,
    page_name=None,
):
    """
    Parse PDF using PyMuPDF.

    Generates:
        - Markdown
        - Extracted images

    Returns
    -------
    dict
    """

    print("Using PyMuPDF Parser")

    input_path = Path(input_path)
    output_dir = Path(output_dir)
    assets_dir = Path(assets_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    if page_name:
        markdown_path = output_dir / f"{page_name}.md"
    else:
        markdown_path = output_dir / "document.md"

    doc = fitz.open(input_path)

    markdown = []

    image_count = 0

    for page in doc:

        

        # --------------------------
        # Extract Text
        # --------------------------

        try:
            text = page.get_text("markdown")
        except Exception:
            text = page.get_text("text")

        markdown.append(text)
        markdown.append("\n\n")

        # --------------------------
        # Extract Images
        # --------------------------

        images = page.get_images(full=True)

        for image in images:

            xref = image[0]

            try:

                base_image = doc.extract_image(xref)

            except Exception:
                continue

            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            image_count += 1

            if page_name:

                image_filename = (
                    f"{page_name}_image_{image_count:04d}.{image_ext}"
                )

            else:

                image_filename = (
                    f"image_{image_count:04d}.{image_ext}"
                )

            image_path = assets_dir / image_filename

            with open(image_path, "wb") as f:
                f.write(image_bytes)

            markdown.append(
                    "<!-- image -->\n\n"
            )

    doc.close()

    markdown_path.write_text(
        "".join(markdown),
        encoding="utf-8",
    )

    return {

        "markdown": markdown_path,

        "assets": assets_dir,

        "image_count": image_count,

    }