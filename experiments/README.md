# Experiments and Research Prototypes

This directory contains standalone exploratory scripts, model benchmarks, and legacy components developed during the research and prototyping phases of `Doc-To-Markdown`.

These files are decoupled from the production document-to-markdown conversion workflow.

---

## Directory Overview

### Research Scripts & Model Experiments

| Script | Purpose & Technology |
|---|---|
| `test_captionllm.py` | Standalone test of `HuggingFaceTB/SmolVLM-500M-Instruct` via HuggingFace Transformers. |
| `test_florence.py` | Standalone test of `microsoft/Florence-2-base` image captioning via Transformers. |
| `test_paddleocr.py` | Benchmark script for PaddleOCR text detection and recognition. |
| `test_ppstructure.py` | Layout analysis and table structure evaluation using PP-StructureV3. |
| `test_rec_boxes.py` | Algorithm prototype for spatial bounding-box grouping and OCR line ordering. |
| `test_pymullmparser.py` | Ad-hoc PyMuPDF4LLM parsing test script. |
| `test_pymupdf4llm.py` | Reference script for PyMuPDF4LLM image extraction. |
| `pymupdf4llm_parser.py` | Standalone PyMuPDF4LLM parser prototype. |

### Legacy Modules (`legacy_modules/`)

These modules represent the earlier two-stage OCR + captioning architecture before transitioning to unified VLM image analysis (`modules/image_analyzer.py`):

| Module | Description |
|---|---|
| `document_processor.py` | Previous multi-document processing runner from the initial Streamlit interface. |
| `ocr_cache.py` | Cache manager for bounding-box OCR detections (`ocr_cache.json`). |
| `rapidocr_parser.py` | RapidOCR text extraction and bounding box spatial reconstruction. |
| `smolvlm_caption.py` | SmolVLM image caption generator with perceptual hash deduplication. |

### Data & Outputs

| Directory / File | Description |
|---|---|
| `ppstructure_test_output/` | Sample JSON and Markdown output generated during PP-Structure testing. |
| `test_benchmark.html` | Sample HTML performance benchmark report. |

