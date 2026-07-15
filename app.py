import streamlit as st
from pathlib import Path
import shutil
import time

from modules.markdown_combiner import combine_markdowns
from modules.doc_converter import convert_doc
from modules.docling_parser import parse_document
from modules.pymupdf_parser import parse_document as parse_document_pymupdf
from modules.rapidocr_parser import extract_ocr_text
from modules.smolvlm_caption import generate_captions
from modules.markdown_merge import merge_markdown
from modules.pdf_analyzer import analyze_pdf
from modules.adaptive_chunker import create_execution_plan
from modules.adaptive_chunker import create_temp_pdf
from modules.utils import clear_folder

# ----------------------------
# Folders
# ----------------------------

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

ASSETS_DIR = Path("assets")
ASSETS_DIR.mkdir(exist_ok=True)



TEMP_CHUNKS_DIR = Path("temp_chunks")
TEMP_CHUNKS_DIR.mkdir(exist_ok=True)

# ----------------------------
# Streamlit
# ----------------------------

st.set_page_config(
    page_title="PDF to Markdown",
    layout="wide"
)

st.title("PDF to Markdown Converter")

uploaded_file = st.file_uploader(
    "Upload PDF, DOC or DOCX",
    type=["pdf", "doc", "docx"]
)

# -------------------------------------------------------
# Main Workflow
# -------------------------------------------------------

if uploaded_file is not None:

    # ----------------------------
    # Clear Previous Outputs
    # ----------------------------

    clear_folder("temp")
    clear_folder("output")
    clear_folder("assets")
    clear_folder("temp_chunks")

    # ----------------------------
    # Save Uploaded File
    # ----------------------------

    uploaded_path = TEMP_DIR / uploaded_file.name

    with open(uploaded_path, "wb") as f:
        shutil.copyfileobj(uploaded_file, f)

    st.success(f"Uploaded : {uploaded_path.name}")

    pipeline_start = time.perf_counter()

    try:

        # ----------------------------
        # Convert DOC -> DOCX
        # ----------------------------

        converted_path = Path(
            convert_doc(uploaded_path)
        )

        st.success("Document preparation completed.")

        # ----------------------------
        # PDF Analysis (Version 3)
        # ----------------------------

        if converted_path.suffix.lower() == ".pdf":

            st.subheader("PDF Analysis")

            analysis_start = time.perf_counter()

            analysis = analyze_pdf(converted_path)

            execution_plan = create_execution_plan(analysis)

            st.subheader("Creating Adaptive Chunks")

            adaptive_chunk_paths = []

            for index, chunk in enumerate(execution_plan):

                chunk_name = f"chunk_{index:04d}"

                temp_pdf = create_temp_pdf(
                    source_pdf=converted_path,
                    start_page=chunk["start_page"],
                    end_page=chunk["end_page"],
                    output_dir=TEMP_CHUNKS_DIR,
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
                    f"Pages {chunk['start_page']} - {chunk['end_page']}"
                )

            st.subheader("Execution Plan")

            for chunk in execution_plan:

                st.write(
                    f"{chunk['parser']} | "
                    f"Pages {chunk['start_page']} - {chunk['end_page']} "
                    f"({chunk['page_count']} pages)"
                )

            analysis_end = time.perf_counter()

            st.info(
                f"PDF Analysis Time : {analysis_end-analysis_start:.2f} seconds"
            )

            st.success("PDF analysis completed.")

            with st.expander("Page Analysis"):

                for page in analysis:

                    st.write(
                        f"Page {page['page']} | "
                        f"Tables : {page['table_count']} | "
                        f"Parser : {page['parser']}"
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
                        output_dir=OUTPUT_DIR,
                        assets_dir=ASSETS_DIR,
                        page_name=chunk_name,
                    )
                    total_images += result["image_count"]

                else:

                    result = parse_document_pymupdf(
                        input_path=chunk_pdf_path,
                        output_dir=OUTPUT_DIR,
                        assets_dir=ASSETS_DIR,
                        page_name=chunk_name,
                    )
                    total_images += result["image_count"]

                chunk_end = time.perf_counter()

                st.write(
                    f"{chunk_name} | "
                    f"{parser} | "
                    f"{chunk_end - chunk_start:.2f} sec"
                )

                total_images += result["image_count"]

                progress.progress(
                    (index + 1) / total_chunks
                )

            parsing_end = time.perf_counter()
            
            st.info(
                f"Parsing Time : {parsing_end - parsing_start:.2f} seconds"
            )

            st.success("Document parsing completed.")    
            st.metric("Images Extracted", total_images)
            markdown_file = combine_markdowns(
                OUTPUT_DIR
            )

        # ----------------------------
        # RapidOCR
        # ----------------------------

        st.subheader("RapidOCR")

        ocr_start = time.perf_counter()

        ocr_results = extract_ocr_text(
            ASSETS_DIR
        )

        ocr_end = time.perf_counter()

        st.info(
            f"RapidOCR Time : {ocr_end-ocr_start:.2f} seconds"
        )

        st.success("OCR completed.")

        # ----------------------------
        # Qwen Captioning
        # ----------------------------

        st.subheader("Image Captioning")

        caption_start = time.perf_counter()

        captions = generate_captions(
            assets_dir=ASSETS_DIR,
            ocr_results=ocr_results
        )

        caption_end = time.perf_counter()

        st.info(
            f"Image Captioning Time : {caption_end-caption_start:.2f} seconds"
        )

        st.success("Image captioning completed.")

        # ----------------------------
        # Markdown Merge
        # ----------------------------

        st.subheader("Generating Final Markdown")

        merge_start = time.perf_counter()

        final_markdown = merge_markdown(
            markdown_path=markdown_file,
            assets_dir=ASSETS_DIR,
            ocr_results=ocr_results,
            captions=captions,
        )

        merge_end = time.perf_counter()

        st.info(
            f"Markdown Merge Time : {merge_end-merge_start:.2f} seconds"
        )

        st.success("Final Markdown Generated")

        st.write("Final Markdown File")

        st.code(str(final_markdown))

        # ----------------------------
        # Download Button
        # ----------------------------

        with open(
            final_markdown,
            "r",
            encoding="utf-8"
        ) as f:

            st.download_button(
                label="Download Markdown",
                data=f.read(),
                file_name="document.md",
                mime="text/markdown",
            )

        pipeline_end = time.perf_counter()

        st.markdown("---")

        st.subheader("Pipeline Performance")

        st.metric(
            "Total Processing Time",
            f"{pipeline_end-pipeline_start:.2f} sec"
        )

        st.write("Stage Breakdown")

        st.write(
            f"📄 Parser(Docling/PyMuPDF) : {parsing_end-parsing_start:.2f} sec"
        )

        st.write(
            f"🔍 RapidOCR : {ocr_end-ocr_start:.2f} sec"
        )

        st.write(
            f"🖼️ Qwen : {caption_end-caption_start:.2f} sec"
        )

        st.write(
            f"📝 Markdown Merge : {merge_end-merge_start:.2f} sec"
        )    

        

    except Exception as e:

        st.error(f"Pipeline Failed\n\n{e}")