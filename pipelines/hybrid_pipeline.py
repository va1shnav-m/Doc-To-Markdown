from pathlib import Path
import streamlit as st
import time

from modules.adaptive_chunker import create_execution_plan
from modules.adaptive_chunker import create_temp_pdf
from modules.pdf_analyzer import analyze_pdf
from modules.docling_parser import parse_document
from modules.pymupdf_parser import parse_document as parse_document_pymupdf
from modules.markdown_combiner import combine_markdowns
from modules.rapidocr_parser import extract_ocr_text
from modules.smolvlm_caption import generate_captions
from modules.markdown_merge import merge_markdown



def process_hybrid_pipeline(
    converted_path,
    output_dir,
    temp_assets_dir,
    temp_chunks_dir,
    document_index,
):
    
    pipeline_start = time.perf_counter()
    analysis_time = 0.0
    chunking_time = 0.0
    parsing_time = 0.0
    ocr_time = 0.0
    caption_time = 0.0
    merge_time = 0.0

    # ----------------------------
    # PDF Analysis 
    # ----------------------------
    if converted_path.suffix.lower() == ".pdf":

        st.subheader("PDF Analysis")

        analysis_start = time.perf_counter()

        print("Before analyze_pdf")
        analysis = analyze_pdf(converted_path)
        print("After analyze_pdf")

        execution_plan = create_execution_plan(analysis)

        

        adaptive_chunk_paths = []

        for index, chunk in enumerate(execution_plan):

            chunk_name = f"chunk_{index:04d}"

            temp_pdf = create_temp_pdf(
                source_pdf=converted_path,
                start_page=chunk["start_page"],
                end_page=chunk["end_page"],
                output_dir=temp_chunks_dir,
                chunk_name=chunk_name,
            )

            adaptive_chunk_paths.append(
                {
                    "pdf": temp_pdf,
                    "parser": chunk["parser"],
                }
            )

            st.write(
                f"{chunk_name} | "
                f"{chunk['parser']} | "
                f"Pages {chunk['start_page']} - {chunk['end_page']} | "
                f"({chunk['page_count']} pages)"
            )

        analysis_end = time.perf_counter()
        analysis_time = analysis_end - analysis_start

        st.info(
            f"PDF Analysis Time : {analysis_time:.2f} seconds"
        )

        st.success(f"Created {len(adaptive_chunk_paths)} adaptive chunks.")

    # ----------------------------
    # Parsing Processing
    # ----------------------------

    st.subheader("Parser Processing")

    parsing_start = time.perf_counter()

    total_images = 0

    progress = st.progress(0)

    if converted_path.suffix.lower() == ".pdf":

        total_chunks = len(adaptive_chunk_paths)

        total_images = 0

        for index, chunk in enumerate(adaptive_chunk_paths):

            chunk_pdf_path = chunk["pdf"]
            parser = chunk["parser"]

            chunk_name = Path(chunk_pdf_path).stem

            chunk_start = time.perf_counter()

            if parser == "docling":

                result = parse_document(
                    input_path=chunk_pdf_path,
                    output_dir=output_dir,
                    assets_dir=temp_assets_dir,
                    page_name=chunk_name,
                )
                total_images += result["image_count"]

            else:

                result = parse_document_pymupdf(
                    input_path=chunk_pdf_path,
                    output_dir=output_dir,
                    assets_dir=temp_assets_dir,
                    page_name=chunk_name,
                )
                total_images += result["image_count"]

            chunk_end = time.perf_counter()

            st.write(
                f"{chunk_name} | "
                f"{parser} | "
                f"{chunk_end - chunk_start:.2f} sec"
            )

            

            progress.progress(
                (index + 1) / total_chunks
            )

        parsing_end = time.perf_counter()
        parsing_time = parsing_end - parsing_start
        
        st.info(
            f"Parsing Time : {parsing_time:.2f} seconds"
        )

        st.success("Document parsing completed.")    
        raw_markdown_name = f"document_{document_index:04d}_raw.md"

        markdown_file = combine_markdowns(
            output_dir,
            output_name=raw_markdown_name,
        )

    else:

        result = parse_document(
            input_path=converted_path,
            output_dir=output_dir,
            assets_dir=temp_assets_dir,
        )

        markdown_file = result["markdown"]

        total_images = result["image_count"]

        parsing_end = time.perf_counter()
        parsing_time = parsing_end - parsing_start

        st.info(
            f"Parsing Time : {parsing_time:.2f} seconds"
        )
        
    progress.empty()    

    # ----------------------------
    # RapidOCR
    # ----------------------------

    st.subheader("RapidOCR")

    ocr_start = time.perf_counter()

    ocr_results = extract_ocr_text(
        temp_assets_dir
    )

    ocr_end = time.perf_counter()
    ocr_time = ocr_end - ocr_start
    st.info(
        f"RapidOCR Time : {ocr_time:.2f} seconds"
    )

    # ----------------------------
    # Qwen Captioning
    # ----------------------------

    st.subheader("Image Captioning")

    caption_start = time.perf_counter()

    captions = generate_captions(
        assets_dir=temp_assets_dir,
        ocr_results=ocr_results
    )

    caption_end = time.perf_counter()
    caption_time = caption_end - caption_start
    st.info(
        f"Image Captioning Time : {caption_time:.2f} seconds"
    )

    # ----------------------------
    # Markdown Merge
    # ----------------------------

    st.subheader("Generating Final Markdown")

    merge_start = time.perf_counter()

    batch_markdown = output_dir / f"document_{document_index:04d}.md"
    
    final_markdown = merge_markdown(
        markdown_path=markdown_file,
        assets_dir=temp_assets_dir,
        ocr_results=ocr_results,
        captions=captions,
        output_path=batch_markdown,
    )

    merge_end = time.perf_counter()
    merge_time = merge_end - merge_start
    st.info(
        f"Markdown Merge Time : {merge_time:.2f} seconds"
    )
    
    pipeline_end = time.perf_counter()

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
        }
    } 