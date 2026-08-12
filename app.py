import streamlit as st
from pathlib import Path
import shutil
import time
from modules.markdown_combiner import combine_final_documents
from modules.doc_converter import convert_doc
from pipelines.docling_pipeline import process_docling_pipeline
from pipelines.hybrid_pipeline import process_hybrid_pipeline
from modules.utils import clear_folder
from modules.reporting import display_report
from benchmark.benchmark import Benchmark
from benchmark.report_generator import generate_benchmark_report
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
        "Docling (Only PDFs are Supported)",
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

    batch_start = time.perf_counter()
    for document_index, uploaded_path in enumerate(uploaded_paths, start=1):

        benchmark = Benchmark()

        benchmark.document_name = uploaded_path.name
        benchmark.document_type = uploaded_path.suffix.lower()
        benchmark.file_size_mb = (
            uploaded_path.stat().st_size / (1024 * 1024)
        )

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

            suffix = uploaded_path.suffix.lower()

            converted_path = uploaded_path

            if suffix == ".doc":
                converted_path = Path(convert_doc(uploaded_path))

            # Parser Selection

            if processing_mode == "Docling (Only PDFs are Supported)":

                # Call the new pipeline
                result = process_docling_pipeline(
                    converted_path=converted_path,
                    output_dir=OUTPUT_DIR,
                    temp_assets_dir=TEMP_ASSETS_DIR,
                    temp_chunks_dir=TEMP_CHUNKS_DIR,
                    document_index=document_index,
                )

            else:

                result = process_hybrid_pipeline(
                    converted_path=converted_path,
                    output_dir=OUTPUT_DIR,
                    temp_assets_dir=TEMP_ASSETS_DIR,
                    temp_chunks_dir=TEMP_CHUNKS_DIR,
                    document_index=document_index,
                )

            final_markdown = result["markdown"]
            total_images = result["image_count"]
            timings = result["timings"]

            # Basic benchmark info
            benchmark.total_time = timings["total"]
            benchmark.images_detected = total_images

            # Stage timings
            benchmark.stage_times = {
                "analysis": timings["analysis"],
                "chunking": timings["chunking"],
                "parsing": timings["parsing"],
                "ocr": timings["ocr"],
                "captioning": timings["caption"],
                "markdown_merge": timings["merge"],
            }

            # Processing report
            report = result["report"]

            # Caption timings
            benchmark.caption_times = result["caption_times"]


            benchmark.images_processed = (
                benchmark.images_detected - benchmark.images_skipped
            )
            
            # OCR metrics
            benchmark.ocr_images = report.ocr_images
            benchmark.ocr_cache_hits = report.ocr_cache_hits
            benchmark.images_skipped = report.ocr_skipped
            benchmark.ocr_failed = report.ocr_failed
            benchmark.ocr_characters = report.ocr_characters

            # Caption metrics
            benchmark.caption_images = (
                report.captions_generated
                + report.captions_cached
                + report.captions_skipped
            )

            benchmark.caption_success = report.captions_generated
            benchmark.caption_failed = report.captions_failed
            benchmark.caption_skipped = report.captions_skipped
            benchmark.caption_cache_hits = report.captions_cached
            benchmark.caption_cache_misses = report.captions_generated

            # Generate report
            benchmark_html = generate_benchmark_report(benchmark)
            # Download button for Report
            st.download_button(
                label="Download Benchmark Report",
                data=benchmark_html,
                file_name=f"{benchmark.document_name}_benchmark.html",
                mime="text/html",
            )

            st.markdown("---")
            st.metric("Images Extracted", total_images)
            st.subheader("Pipeline Performance")

            st.metric(
                "Total Processing Time",
                f"{timings['total']:.2f} sec"
            )

            if timings["analysis"] > 0:
                st.write(f"PDF Analysis : {timings['analysis']:.2f} sec")

            if timings["chunking"] > 0:
                st.write(f"PDF Chunking : {timings['chunking']:.2f} sec")

            st.write(f"Parsing : {timings['parsing']:.2f} sec")
            st.write(f"RapidOCR : {timings['ocr']:.2f} sec")
            st.write(f"SmolVLM : {timings['caption']:.2f} sec")
            st.write(f"Markdown Merge : {timings['merge']:.2f} sec")
            display_report(report)
        except Exception as e:

            st.error(f"Pipeline Failed\n\n{e}")
    batch_time = time.perf_counter() - batch_start

    st.markdown("---")
    st.subheader("Batch Performance")

    st.metric(
        "Total Batch Processing Time",
        f"{batch_time:.2f} sec"
    )        
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