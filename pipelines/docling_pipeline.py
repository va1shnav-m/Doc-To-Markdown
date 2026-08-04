from pathlib import Path
import streamlit as st
import time
from modules.document_chunker import chunk_pdf
from modules.docling_parser import parse_document
from modules.markdown_combiner import combine_markdowns
from modules.rapidocr_parser import extract_ocr_text
from modules.smolvlm_caption import generate_captions
from modules.markdown_merge import merge_markdown
from modules.reporting import ProcessingReport
from modules.ui import StreamlitUI


def process_docling_pipeline(
    converted_path,
    output_dir,
    temp_assets_dir,
    temp_chunks_dir,
    document_index,
    ui=None,
):

    pipeline_start = time.perf_counter()
    analysis_time = 0.0
    chunking_time = 0.0
    parsing_time = 0.0
    ocr_time = 0.0
    caption_time = 0.0
    merge_time = 0.0
    if ui is None:
        ui = StreamlitUI()
    total_images = 0

    report = ProcessingReport()

    report.input_file = converted_path.name
    # ----------------------------------------
    # Split PDF into chunks
    # ----------------------------------------
    ui.subheader("PDF Chunking")
    chunk_start = time.perf_counter()
    chunk_paths = chunk_pdf(
        pdf_path=converted_path,
        output_folder=temp_chunks_dir,
        chunk_size=25,
    )
    chunk_end = time.perf_counter()
    chunking_time = chunk_end - chunk_start
    ui.info(
        f"Chunking Time : {chunking_time:.2f} seconds"
    )

    ui.success(f"Created {len(chunk_paths)} chunks.")

    # ----------------------------------------
    # Parse each chunk using Docling
    # ----------------------------------------
    ui.subheader("Docling Processing")
    parsing_start = time.perf_counter()
    progress = ui.progress(0)
    total_chunks = len(chunk_paths)

    for index, chunk_path in enumerate(chunk_paths):

        chunk_name = Path(chunk_path).stem
        chunk_stage_start=time.perf_counter()
        result = parse_document(
            input_path=chunk_path,
            output_dir=output_dir,
            assets_dir=temp_assets_dir,
            page_name=chunk_name,
        )
        chunk_stage_end = time.perf_counter()

        total_images += result["image_count"]
        ui.write(
            f"{chunk_name} | "
            f"{chunk_stage_end - chunk_stage_start:.2f} sec"
        )
        progress.progress((index + 1) / total_chunks)
      
    parsing_end = time.perf_counter()
    parsing_time = parsing_end - parsing_start
    ui.info(
        f"Docling Processing Time : {parsing_time:.2f} seconds"
    )
    progress.empty()
    
        

    # ----------------------------------------
    # Combine all chunk markdowns
    # ----------------------------------------

    raw_markdown_name = f"document_{document_index:04d}_raw.md"

    markdown_file = combine_markdowns(
        output_dir=output_dir,
        output_name=raw_markdown_name,
    )

    # ----------------------------------------
    # OCR
    # ----------------------------------------
    ui.subheader("RapidOCR")
    ocr_start = time.perf_counter()
    ocr_result = extract_ocr_text(
        temp_assets_dir
    )

    ocr_results = ocr_result["results"]

    report.ocr_images = ocr_result["ocr_image_count"]

    ocr_end = time.perf_counter()
    ocr_time = ocr_end - ocr_start
    ui.info(
        f"RapidOCR Time : {ocr_time:.2f} seconds"
    )
    # ----------------------------------------
    # Image Captioning
    # ----------------------------------------
    ui.subheader("Image Captioning")
    caption_start = time.perf_counter()
    caption_result = generate_captions(
        assets_dir=temp_assets_dir,
        ocr_results=ocr_results,
    )

    captions = caption_result["captions"]

    report.captions_generated = caption_result["generated"]
    report.captions_cached = caption_result["cached"]
    report.captions_skipped = caption_result["skipped"]
    caption_end = time.perf_counter()
    caption_time = caption_end - caption_start
    ui.info(
        f"SmolVLM Time : {caption_time:.2f} seconds"
    )
    # ----------------------------------------
    # Final Markdown
    # ----------------------------------------

    final_output = output_dir / f"document_{document_index:04d}.md"
    ui.subheader("Generating Final Markdown")
    merge_start = time.perf_counter()
    final_markdown = merge_markdown(
        markdown_path=markdown_file,
        assets_dir=temp_assets_dir,
        ocr_results=ocr_results,
        captions=captions,
        output_path=final_output,
    )
    merge_end = time.perf_counter()
    merge_time = merge_end - merge_start
    ui.info(
        f"Markdown Merge Time : {merge_time:.2f} seconds"
    )
    pipeline_end = time.perf_counter()
    report.output_file = final_markdown.name

    report.images_extracted = total_images

    report.analysis_time = analysis_time
    report.chunking_time = chunking_time
    report.parsing_time = parsing_time
    report.ocr_time = ocr_time
    report.caption_time = caption_time
    report.merge_time = merge_time
    report.total_time = pipeline_end - pipeline_start

    return {
        "markdown": final_markdown,
        "image_count": total_images,
        "timings": {
            "analysis": analysis_time,
            "chunking": chunking_time,
            "parsing": parsing_time,
            "ocr": ocr_time,
            "caption": caption_time,
            "merge": merge_time,
            "total": pipeline_end - pipeline_start,
        },
        "report": report
    }