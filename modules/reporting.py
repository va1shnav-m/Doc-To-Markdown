from dataclasses import dataclass, field
from typing import List
import streamlit as st

@dataclass
class ProcessingReport:

    input_file: str = ""
    output_file: str = ""

    total_pages: int = 0

    pymupdf_pages: int = 0
    docling_pages: int = 0

    tables_found: int = 0
    images_extracted: int = 0
    ocr_images: int = 0

    captions_generated: int = 0
    captions_cached: int = 0
    captions_skipped: int = 0

    analysis_time: float = 0.0
    chunking_time: float = 0.0
    parsing_time: float = 0.0
    ocr_time: float = 0.0
    caption_time: float = 0.0
    merge_time: float = 0.0
    total_time: float = 0.0

    warnings: List[str] = field(default_factory=list)

    def add_warning(self, message):
        self.warnings.append(message)


def display_report(report):

    st.markdown("---")
    st.header("📄 Document Processing Summary")

    # ---------------------------------------
    # Document Information
    # ---------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Input File", report.input_file)

    with col2:
        st.metric("Output File", report.output_file)

    # ---------------------------------------
    # Parser Statistics
    # ---------------------------------------

    st.subheader("Parser Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Pages", report.total_pages)

    with col2:
        st.metric("PyMuPDF", report.pymupdf_pages)

    with col3:
        st.metric("Docling", report.docling_pages)

    with col4:
        st.metric("Tables", report.tables_found)

    # ---------------------------------------
    # Content Statistics
    # ---------------------------------------

    st.subheader("Content Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Images", report.images_extracted)

    with col2:
        st.metric("OCR Images", report.ocr_images)

    with col3:
        st.metric("Generated", report.captions_generated)

    with col4:
        st.metric("Cached", report.captions_cached)

    # Second row

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Skipped", report.captions_skipped)

    with col2:
        st.metric("Warnings", len(report.warnings))

    # ---------------------------------------
    # Performance
    # ---------------------------------------

    st.subheader("Performance")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Analysis", f"{report.analysis_time:.2f}s")

    with col2:
        st.metric("Parsing", f"{report.parsing_time:.2f}s")

    with col3:
        st.metric("OCR", f"{report.ocr_time:.2f}s")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Caption", f"{report.caption_time:.2f}s")

    with col2:
        st.metric("Merge", f"{report.merge_time:.2f}s")

    with col3:
        st.metric("Total", f"{report.total_time:.2f}s")

    # ---------------------------------------
    # Warnings
    # ---------------------------------------

    if report.warnings:

        st.subheader("Warnings")

        for warning in report.warnings:
            st.warning(warning)