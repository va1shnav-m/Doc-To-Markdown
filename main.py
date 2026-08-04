import argparse
from pathlib import Path
from modules.ui import ConsoleUI
from modules.doc_converter import convert_doc
from modules.utils import clear_folder

from pipelines.hybrid_pipeline import process_hybrid_pipeline
from pipelines.docling_pipeline import process_docling_pipeline

parser = argparse.ArgumentParser(
    description="Document Parser CLI"
)

subparser = parser.add_subparsers(dest="command")

convert = subparser.add_parser("convert")

convert.add_argument(
    "input_folder",
    help="Folder containing documents"
)

convert.add_argument(
    "--out",
    required=True,
    help="Output folder"
)

convert.add_argument(
    "--no-ocr",
    action="store_true"
)

convert.add_argument(
    "--no-caption",
    action="store_true"
)

convert.add_argument(
    "--force",
    action="store_true"
)

args = parser.parse_args()

if args.command == "convert":

    input_folder = Path(args.input_folder)
    output_folder = Path(args.out)
    ui = ConsoleUI()
    if not input_folder.exists():
        print(f"Input folder not found: {input_folder}")
        exit(1)

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    print(f"Input Folder : {input_folder}")
    print(f"Output Folder: {output_folder}")
    print(f"No OCR       : {args.no_ocr}")
    print(f"No Caption   : {args.no_caption}")
    print(f"Force        : {args.force}")

    supported_extensions = {
        ".pdf",
        ".docx",
        ".doc"
    }

    documents = []

    for file in input_folder.rglob("*"):

        if file.suffix.lower() in supported_extensions:
            documents.append(file)

    print("\nDocuments Found")

    if not documents:
        print("No supported documents found.")
        exit(0)

    for index, document in enumerate(documents, start=1):

        print("\n" + "=" * 60)
        print(f"Processing {index}/{len(documents)}")
        print(document.name)
        print("=" * 60)

        clear_folder("temp_assets")
        clear_folder("temp_chunks")

        converted_path = document

        if document.suffix.lower() == ".doc":
            converted_path = Path(
                convert_doc(document)
            )

        result = process_hybrid_pipeline(
            converted_path=converted_path,
            output_dir=output_folder,
            temp_assets_dir=Path("temp_assets"),
            temp_chunks_dir=Path("temp_chunks"),
            document_index=index,
            ui=ui,
        )

        print(f"\nCompleted : {result['markdown']}")