from pathlib import Path
import subprocess

# Path to LibreOffice
SOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"


def convert_doc(file_path):
    """
    Converts a .doc file to .docx using LibreOffice Headless.
    If the file is already a PDF or DOCX, it is returned unchanged.

    Parameters:
        file_path (str): Path to the uploaded document.

    Returns:
        str: Path to the converted or original file.
    """

    file_path = Path(file_path)

    # If not a .doc file, no conversion is needed.
    if file_path.suffix.lower() != ".doc":
        return str(file_path)

    output_dir = file_path.parent

    subprocess.run(
        [
            SOFFICE_PATH,
            "--headless",
            "--convert-to",
            "docx",
            "--outdir",
            str(output_dir),
            str(file_path),
        ],
        check=True,
    )

    converted_file = output_dir / f"{file_path.stem}.docx"

    return str(converted_file)