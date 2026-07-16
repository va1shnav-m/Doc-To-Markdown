from pathlib import Path
import fitz


# Images covering more than 10% of the page
# are considered important.
IMAGE_AREA_THRESHOLD = 0.10


def analyze_pdf(pdf_path):
    """
    Analyze each page and decide which parser to use.

    Docling:
        - Tables
        - Large images / diagrams / screenshots

    PyMuPDF:
        - Plain digital text
    """

    pdf_path = Path(pdf_path)

    doc = fitz.open(pdf_path)

    analysis = []

    print("\n========== PDF ANALYSIS ==========\n")

    for page_index, page in enumerate(doc):

        page_number = page_index + 1

        # ----------------------------------
        # Detect Tables
        # ----------------------------------

        try:
            tables = page.find_tables()
            table_count = len(tables.tables)

        except Exception:

            table_count = 0

        fallback_table = likely_has_table(page)

        has_table = (
            table_count > 0
            or fallback_table
        )

        if table_count == 0 and fallback_table:
            table_count = 1


        # ----------------------------------
        # Detect Images
        # ----------------------------------

        images = page.get_images(full=True)

        image_count = len(images)

        page_rect = page.rect
        page_area = page_rect.width * page_rect.height

        largest_image_ratio = 0.0

        for image in images:

            xref = image[0]

            try:

                rects = page.get_image_rects(xref)

            except Exception:

                continue

            for rect in rects:

                image_area = rect.width * rect.height

                ratio = image_area / page_area

                if ratio > largest_image_ratio:

                    largest_image_ratio = ratio

        has_large_image = (
            largest_image_ratio >= IMAGE_AREA_THRESHOLD
        )

        # ----------------------------------
        # Select Parser
        # ----------------------------------

        if has_table:

            parser = "docling"

        elif has_large_image:

            parser = "docling"

        else:

            parser = "pymupdf"

        page_info = {

            "page": page_number,

            "has_table": has_table,

            "table_count": table_count,

            "image_count": image_count,

            "largest_image_ratio": round(
                largest_image_ratio,
                3
            ),

            "parser": parser,

        }

        analysis.append(page_info)

        print(
            f"Page {page_number:03d} | "
            f"Tables: {table_count:<2} | "
            f"Images: {image_count:<2} | "
            f"Largest: {largest_image_ratio:.2f} | "
            f"Parser: {parser}"
        )

    doc.close()

    print("\n========== ANALYSIS COMPLETE ==========\n")

    return analysis

def likely_has_table(page):
    """
    Fallback heuristic for borderless tables.
    Detects row-column structures instead of simple indentation.
    """

    blocks = page.get_text("blocks")

    if len(blocks) < 5:
        return False

    # Group blocks by Y position (same row)
    rows = {}

    for block in blocks:
        x0, y0 = round(block[0], 1), round(block[1], 1)

        # Merge nearby Y values into the same row
        row_key = round(y0 / 5) * 5

        rows.setdefault(row_key, []).append(x0)

    row_like_count = 0

    for xs in rows.values():

        # Ignore duplicate X values in a row
        unique_x = len(set(xs))

        # A table row usually has multiple columns
        if unique_x >= 3:
            row_like_count += 1

    # Require several rows with multiple columns
    return row_like_count >= 3