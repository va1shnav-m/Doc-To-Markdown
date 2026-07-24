from pathlib import Path
import fitz  # PyMuPDF


def chunk_pdf(
    pdf_path,
    output_folder,
    chunk_size=15,
):
    """
    Split a PDF into multi-page chunks.

    Parameters
    ----------
    pdf_path : str | Path

    output_folder : str | Path

    chunk_size : int
        Number of pages per chunk.

    Returns
    -------
    list
        List of generated chunk PDF paths.
    """

    pdf_path = Path(pdf_path)
    output_folder = Path(output_folder)

    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    document = fitz.open(pdf_path)

    chunk_paths = []

    total_pages = len(document)

    chunk_number = 1

    for start_page in range(0, total_pages, chunk_size):

        end_page = min(
            start_page + chunk_size - 1,
            total_pages - 1,
        )

        chunk_pdf = fitz.open()

        chunk_pdf.insert_pdf(
            document,
            from_page=start_page,
            to_page=end_page,
        )

        output_path = (
            output_folder
            / f"chunk_{chunk_number:04d}.pdf"
        )

        chunk_pdf.save(output_path)
        chunk_pdf.close()

        chunk_paths.append(output_path)

        chunk_number += 1

    document.close()

    return chunk_paths