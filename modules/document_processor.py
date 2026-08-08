from pathlib import Path
import time

from modules.doc_converter import convert_doc
from pipelines.hybrid_pipeline import process_hybrid_pipeline
from pipelines.docling_pipeline import process_docling_pipeline


def process_documents(
    uploaded_paths,
    processing_mode,
    output_dir,
    temp_assets_dir,
    temp_chunks_dir,
    clear_folder,
):
    """
    Process one or more documents using the selected pipeline.

    uploaded_paths : list[Path]
    processing_mode : str
    """

    for document_index, uploaded_path in enumerate(uploaded_paths, start=1):

        clear_folder("temp_assets")
        clear_folder("temp_chunks")

        for chunk_file in output_dir.glob("chunk_*.md"):
            chunk_file.unlink()

        print(
            f"\nProcessing {document_index}/{len(uploaded_paths)}"
        )

        print(uploaded_path.name)

        pipeline_start = time.perf_counter()

        suffix = uploaded_path.suffix.lower()

        converted_path = uploaded_path

        if suffix == ".doc":
            converted_path = Path(convert_doc(uploaded_path))

        if processing_mode == "Docling (Only PDFs are Supported)":

            result = process_docling_pipeline(
                converted_path=converted_path,
                output_dir=output_dir,
                temp_assets_dir=temp_assets_dir,
                temp_chunks_dir=temp_chunks_dir,
                document_index=document_index,
            )

        else:

            result = process_hybrid_pipeline(
                converted_path=converted_path,
                output_dir=output_dir,
                temp_assets_dir=temp_assets_dir,
                temp_chunks_dir=temp_chunks_dir,
                document_index=document_index,
            )

        print(
            f"Completed in {time.perf_counter() - pipeline_start:.2f} seconds"
        )