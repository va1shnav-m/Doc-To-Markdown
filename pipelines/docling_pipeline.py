from pathlib import Path
import streamlit as st
import time
from modules.document_chunker import chunk_pdf
from modules.docling_parser import parse_document
from modules.markdown_combiner import combine_markdowns
from modules.rapidocr_parser import extract_ocr_text
from modules.smolvlm_caption import generate_captions
from modules.markdown_merge import merge_markdown


def process_docling_pipeline(
    converted_path,
    output_dir,
    temp_assets_dir,
    temp_chunks_dir,
    document_index,
):

    pipeline_start = time.perf_counter()

    # ----------------------------------------
    # Split PDF into chunks
    # ----------------------------------------
    st.subheader("PDF Chunking")
    chunk_start = time.perf_counter()
    chunk_paths = chunk_pdf(
        pdf_path=converted_path,
        output_folder=temp_chunks_dir,
        chunk_size=25,
    )
    chunk_end = time.perf_counter()
    st.info(
        f"Chunking Time : {chunk_end - chunk_start:.2f} seconds"
    )

    st.success(f"Created {len(chunk_paths)} chunks.")


    total_images = 0

    # ----------------------------------------
    # Parse each chunk using Docling
    # ----------------------------------------
    st.subheader("Docling Processing")
    docling_start = time.perf_counter()
    total_images=0
    for chunk_path in chunk_paths:

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
        st.write(
            f"{chunk_name} | "
            f"{chunk_stage_end - chunk_stage_start:.2f} sec"
        )
    docling_end = time.perf_counter()
    st.info(
        f"Docling Processing Time : {docling_end - docling_start:.2f} seconds"
    )

    st.metric(
        "Images Extracted",
        total_images
    )
        

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
    st.subheader("RapidOCR")
    ocr_start = time.perf_counter()
    ocr_results = extract_ocr_text(
        temp_assets_dir
    )

    ocr_end = time.perf_counter()
    st.info(
        f"RapidOCR Time : {ocr_end - ocr_start:.2f} seconds"
    )
    # ----------------------------------------
    # Image Captioning
    # ----------------------------------------
    st.subheader("Image Captioning")
    caption_start = time.perf_counter()
    captions = generate_captions(
        assets_dir=temp_assets_dir,
        ocr_results=ocr_results,
    )
    caption_end = time.perf_counter()
    st.info(
        f"SmolVLM Time : {caption_end - caption_start:.2f} seconds"
    )
    # ----------------------------------------
    # Final Markdown
    # ----------------------------------------

    final_output = output_dir / f"document_{document_index:04d}.md"
    st.subheader("Generating Final Markdown")
    merge_start = time.perf_counter()
    final_markdown = merge_markdown(
        markdown_path=markdown_file,
        assets_dir=temp_assets_dir,
        ocr_results=ocr_results,
        captions=captions,
        output_path=final_output,
    )
    merge_end = time.perf_counter()
    st.info(
        f"Markdown Merge Time : {merge_end - merge_start:.2f} seconds"
    )
    pipeline_end = time.perf_counter()
    
    return {
        "markdown": final_markdown,
        "image_count": total_images,
        "timings": {
            "chunking": chunk_end - chunk_start,
            "docling": docling_end - docling_start,
            "ocr": ocr_end - ocr_start,
            "caption": caption_end - caption_start,
            "merge": merge_end - merge_start,
            "total": pipeline_end - pipeline_start,
        },
    }