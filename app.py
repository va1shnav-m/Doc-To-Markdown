import streamlit as st
from pathlib import Path
import shutil
import time

from modules.markdown_combiner import combine_markdowns
from modules.markdown_combiner import combine_final_documents
from modules.doc_converter import convert_doc
from modules.docling_parser import parse_document
# from modules.pymupdf_parser import parse_document as parse_document_pymupdf
from modules.rapidocr_parser import extract_ocr_text
from modules.smolvlm_caption import generate_captions
from modules.markdown_merge import merge_markdown
from modules.pdf_analyzer import analyze_pdf
from modules.adaptive_chunker import create_execution_plan
from modules.adaptive_chunker import create_temp_pdf
from pipelines.docling_pipeline import process_docling_pipeline
from modules.pymupdf4llm_parser import parse_document as parse_document_pymupdf
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

TEMP_ASSETS_DIR = Path("temp_assets")
TEMP_ASSETS_DIR.mkdir(exist_ok=True)

TEMP_CHUNKS_DIR = Path("temp_chunks")
TEMP_CHUNKS_DIR.mkdir(exist_ok=True)

# ----------------------------
# Streamlit
# ----------------------------

st.set_page_config(
    page_title="PDF to Markdown",
    layout="wide"
)

st.title("PDF/DOC/DOCX to Markdown Conversion")

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

uploaded_file = st.file_uploader(
    "Upload PDF, DOC or DOCX",
    type=["pdf", "doc", "docx"]
    )

processing_mode = st.radio(
    "Processing Mode",
    [
        "PyMuPDF + Docling",
        "Docling Only",
    ],
    horizontal=True,
)

# Store uploaded files
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# Add uploaded file to the list
if uploaded_file and uploaded_file.name not in [
    f.name for f in st.session_state.uploaded_files
]:
    st.session_state.uploaded_files.append(uploaded_file)

# Show uploaded files
st.subheader("Uploaded Files")

for index, file in enumerate(
    st.session_state.uploaded_files,
    start=1
):
    st.write(f"{index}. {file.name}")

if st.button("Start Processing") and st.session_state.uploaded_files:

    # ----------------------------
    # Clear Previous Outputs
    # ----------------------------

    clear_folder("temp")
    clear_folder("output")
    clear_folder("assets")
    
    # ----------------------------
    # Save Uploaded File
    # ----------------------------

    uploaded_paths = []

    for uploaded_file in st.session_state.uploaded_files:

        uploaded_path = TEMP_DIR / uploaded_file.name

        with open(uploaded_path, "wb") as f:
            shutil.copyfileobj(uploaded_file, f)

        uploaded_paths.append(uploaded_path)

        st.success(f"Uploaded : {uploaded_path.name}")

    for document_index, uploaded_path in enumerate(uploaded_paths, start=1):

        clear_folder("temp_assets")
        clear_folder("temp_chunks")

        for chunk_file in OUTPUT_DIR.glob("chunk_*.md"):
            chunk_file.unlink()

        st.markdown("---")
        st.subheader(
            f"Processing Document {document_index} of {len(uploaded_paths)}"
        )
        st.write(uploaded_path.name)    

        pipeline_start = time.perf_counter()

        try:

            # ----------------------------
            # Convert DOC -> DOCX
            # ----------------------------

            converted_path = Path(
                convert_doc(uploaded_path)
            )

            if processing_mode == "Docling Only":

                # Call the new pipeline
                result = process_docling_pipeline(
                    converted_path=converted_path,
                    output_dir=OUTPUT_DIR,
                    temp_assets_dir=TEMP_ASSETS_DIR,
                    temp_chunks_dir=TEMP_CHUNKS_DIR,
                    document_index=document_index,
                )
                
                final_markdown = result["markdown"]
                total_images = result["image_count"]
                timings = result["timings"]

                st.markdown("---")
                st.metric("Images Extracted", total_images)
                st.subheader("Pipeline Performance")

                st.metric(
                    "Total Processing Time",
                    f"{timings['total']:.2f} sec"
                )

                st.write(
                    f"PDF Chunking : {timings['chunking']:.2f} sec"
                )

                st.write(
                    f"Docling Parsing : {timings['docling']:.2f} sec"
                )

                st.write(
                    f"RapidOCR : {timings['ocr']:.2f} sec"
                )

                st.write(
                    f"SmolVLM : {timings['caption']:.2f} sec"
                )

                st.write(
                    f"Markdown Merge : {timings['merge']:.2f} sec"
                )
            else:

                 # ----------------------------
                 # PDF Analysis 
                 # ----------------------------

                if converted_path.suffix.lower() == ".pdf":

                    st.subheader("PDF Analysis")

                    analysis_start = time.perf_counter()

                    analysis = analyze_pdf(converted_path)

                    execution_plan = create_execution_plan(analysis)

                    

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
                            f"Pages {chunk['start_page']} - {chunk['end_page']} | "
                            f"({chunk['page_count']} pages)"
                        )

                    analysis_end = time.perf_counter()

                    st.info(
                        f"PDF Analysis Time : {analysis_end-analysis_start:.2f} seconds"
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
                                assets_dir=TEMP_ASSETS_DIR,
                                page_name=chunk_name,
                            )
                            total_images += result["image_count"]

                        else:

                            result = parse_document_pymupdf(
                                input_path=chunk_pdf_path,
                                output_dir=OUTPUT_DIR,
                                assets_dir=TEMP_ASSETS_DIR,
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
                    
                    st.info(
                        f"Parsing Time : {parsing_end - parsing_start:.2f} seconds"
                    )

                    st.success("Document parsing completed.")    
                    st.metric("Images Extracted", total_images)
                    raw_markdown_name = f"document_{document_index:04d}_raw.md"

                    markdown_file = combine_markdowns(
                        OUTPUT_DIR,
                        output_name=raw_markdown_name,
                    )

                else:

                    result = parse_document(
                        input_path=converted_path,
                        output_dir=OUTPUT_DIR,
                        assets_dir=TEMP_ASSETS_DIR,
                    )

                    markdown_file = result["markdown"]

                    total_images = result["image_count"]

                    parsing_end = time.perf_counter()

                    st.info(
                        f"Parsing Time : {parsing_end - parsing_start:.2f} seconds"
                    )

                    st.metric(
                        "Images Extracted",
                        total_images
                )

                progress.empty()    

                # ----------------------------
                # RapidOCR
                # ----------------------------

                st.subheader("RapidOCR")

                ocr_start = time.perf_counter()

                ocr_results = extract_ocr_text(
                    TEMP_ASSETS_DIR
                )

                ocr_end = time.perf_counter()

                st.info(
                    f"RapidOCR Time : {ocr_end-ocr_start:.2f} seconds"
                )

                # ----------------------------
                # Qwen Captioning
                # ----------------------------

                st.subheader("Image Captioning")

                caption_start = time.perf_counter()

                captions = generate_captions(
                    assets_dir=TEMP_ASSETS_DIR,
                    ocr_results=ocr_results
                )

                caption_end = time.perf_counter()

                st.info(
                    f"Image Captioning Time : {caption_end-caption_start:.2f} seconds"
                )

                # ----------------------------
                # Markdown Merge
                # ----------------------------

                st.subheader("Generating Final Markdown")

                merge_start = time.perf_counter()

                batch_markdown = OUTPUT_DIR / f"document_{document_index:04d}.md"
                
                final_markdown = merge_markdown(
                    markdown_path=markdown_file,
                    assets_dir=TEMP_ASSETS_DIR,
                    ocr_results=ocr_results,
                    captions=captions,
                    output_path=batch_markdown,
                )

                merge_end = time.perf_counter()

                st.info(
                    f"Markdown Merge Time : {merge_end-merge_start:.2f} seconds"
                )

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
                        file_name=final_markdown.name,
                        mime="text/markdown",
                        key=f"download_{document_index}",
                    )

                pipeline_end = time.perf_counter()

                st.markdown("---")

                st.subheader("Pipeline Performance")

                st.metric(
                    "Total Processing Time",
                    f"{pipeline_end-pipeline_start:.2f} sec"
                )

                st.write(
                    f" Parser(Docling/PyMuPDF) : {parsing_end-parsing_start:.2f} sec"
                )

                st.write(
                    f" RapidOCR : {ocr_end-ocr_start:.2f} sec"
                )

                st.write(
                    f" SmolVLM : {caption_end-caption_start:.2f} sec"
                )

                st.write(
                    f" Markdown Merge : {merge_end-merge_start:.2f} sec"
                )    

            

        except Exception as e:

            st.error(f"Pipeline Failed\n\n{e}")
            
    final_batch = combine_final_documents(OUTPUT_DIR)

    st.success("Combined markdown created.")

    st.code(str(final_batch))        

    with open(final_batch, "r", encoding="utf-8") as f:

        st.download_button(
            label="Download Combined Markdown",
            data=f.read(),
            file_name=final_batch.name,
            mime="text/markdown",
            key="download_combined_markdown",
        )