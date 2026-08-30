"""Core modules for document parsing, analysis, and processing."""

from .adaptive_chunker import create_execution_plan, create_temp_pdf
from .doc_converter import convert_doc
from .docling_parser import parse_document as parse_docling
from .document_chunker import chunk_pdf
from .image_analyzer import analyze_images
from .image_filter import should_process
from .markdown_combiner import combine_markdowns, combine_final_documents
from .markdown_merge import merge_markdown
from .ollama_utils import is_ollama_running, ensure_ollama_running
from .pdf_analyzer import analyze_pdf
from .pymupdf_parser import parse_document as parse_pymupdf
from .reporting import ProcessingReport, print_report
from .ui import ConsoleUI
from .utils import clear_folder

__all__ = [
    "create_execution_plan",
    "create_temp_pdf",
    "convert_doc",
    "parse_docling",
    "chunk_pdf",
    "analyze_images",
    "should_process",
    "combine_markdowns",
    "combine_final_documents",
    "merge_markdown",
    "is_ollama_running",
    "ensure_ollama_running",
    "analyze_pdf",
    "parse_pymupdf",
    "ProcessingReport",
    "print_report",
    "ConsoleUI",
    "clear_folder",
]

