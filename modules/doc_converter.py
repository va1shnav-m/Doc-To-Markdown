from pathlib import Path
import subprocess

import os
import shutil

def _find_soffice():
    """Locate the LibreOffice / soffice executable across platforms."""
    custom_path = os.getenv("LIBREOFFICE_PATH")
    if custom_path and Path(custom_path).exists():
        return custom_path

    # Check PATH (works on Linux, macOS, and Windows if in PATH)
    which_soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if which_soffice:
        return which_soffice

    # Common Windows install locations
    windows_paths = [
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
    ]
    for p in windows_paths:
        if p.exists():
            return str(p)

    return "soffice"

SOFFICE_PATH = _find_soffice()


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