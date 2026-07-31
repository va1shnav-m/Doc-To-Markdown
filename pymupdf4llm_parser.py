from pathlib import Path
import fitz
import re
import pymupdf4llm
#import itertools

# def format_heading(text: str, font: str) -> str:
#     """
#     Convert numbered headings to Markdown headings.
#     """

#     text = text.strip()
    
#     # 1.2.3 Heading
#     if re.match(r"^\d+\.\d+\.\d+\b", text):
#         return f"### {text}"

#     # 1.2 Heading
#     if re.match(r"^\d+\.\d+\b", text):
#         return f"## {text}"

#     # 1. Heading
#     if re.match(r"^\d+\.\b", text):
#         return f"# {text}"

#     # Common unnumbered headings
#     if text.lower() in {
#         "references",
#         "appendix",
#         "glossary",
#         "revision history",
#         "table of contents",
#     }:
#         return f"# {text}"

#     return text

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
    
    markdown = pymupdf4llm.to_markdown(
        doc,
        write_images=True,
        image_path=str(assets_dir),
    )
    # Replace markdown image links with placeholder
    markdown = re.sub(
        r'!\[.*?\]\(.*?\)',
        '<!-- image -->',
        markdown
    )

    # Remove PyMuPDF4LLM picture text blocks
    markdown = re.sub(
        r'<!-- Start of picture text -->.*?<!-- End of picture text -->',
        '',
        markdown,
        flags=re.DOTALL
    )
    image_count = markdown.count("<!-- image -->")
    
    # pattern = (
    #     r"<!-- Start of picture text -->"
    #     r".*?"
    #     r"<!-- End of picture text -->"
    # )

    # placeholder_counter = itertools.count(1)

    # def replace_placeholder(match):
    #     image_no = next(placeholder_counter)
    #     return f"\n\n<!-- assets/image_{image_no:04d}.png -->\n\n"

    # markdown = re.sub(
    #     pattern,
    #     replace_placeholder,
    #     markdown,
    #     flags=re.DOTALL,
    # )
    

    # image_count = 0

    # for page in doc:

    #     # --------------------------
    #     # Extract Images
    #     # --------------------------

    #     images = page.get_images(full=True)

    #     for image in images:

    #         xref = image[0]

    #         try:
    #             base_image = doc.extract_image(xref)
    #         except Exception:
    #             continue

    #         image_bytes = base_image["image"]
    #         image_ext = base_image["ext"]

    #         image_count += 1

    #         if page_name:
    #             image_filename = (
    #                 f"{page_name}_image_{image_count:04d}.{image_ext}"
    #             )
    #         else:
    #             image_filename = (
    #                 f"image_{image_count:04d}.{image_ext}"
    #             )

    #         image_path = assets_dir / image_filename

    #         with open(image_path, "wb") as f:
    #             f.write(image_bytes)
    
    doc.close()

    markdown_path.write_text(
        markdown,
        encoding="utf-8",
    )

    return {
        "markdown": markdown_path,
        "assets": assets_dir,
        "image_count": image_count,
    }