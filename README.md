<![CDATA[<div align="center">

# 📄 Doc-To-Markdown

**Intelligent document-to-Markdown converter optimized for RAG workflows**

[![CI](https://github.com/va1shnav-m/Doc-To-Markdown/actions/workflows/ci.yml/badge.svg)](https://github.com/va1shnav-m/Doc-To-Markdown/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

Convert **PDF**, **DOC**, and **DOCX** files into clean, structured Markdown — preserving tables, images, and document hierarchy — purpose-built for Retrieval-Augmented Generation (RAG) pipelines.

</div>

---

## ✨ Features

- **Multi-format support** — PDF, DOC, and DOCX input files
- **Hybrid parsing pipeline** — Intelligently routes pages to Docling (complex pages with tables/images) or PyMuPDF (standard text pages) for optimal accuracy
- **Adaptive chunking** — Splits large PDFs into parser-aware chunks to prevent memory issues
- **AI-powered image analysis** — Classifies images as *technical* or *general*, extracts text, and generates structured descriptions using a Vision-Language Model (VLM)
- **Perceptual hash caching** — Deduplicates image analysis using pHash to avoid redundant VLM calls
- **Smart image filtering** — Skips tiny, solid-colour, and extreme-aspect-ratio images automatically
- **Table detection** — Detects bordered, borderless, and rectangle-based tables via vector analysis and PyMuPDF's built-in table finder
- **Benchmark reports** — Generates per-document HTML benchmark reports with stage-level timing breakdowns
- **Batch processing** — Process entire folders of documents in a single run
- **Docker support** — Containerized deployment with Docker Compose

---

## 🏗️ Architecture

### Hybrid Pipeline (PDF)

```
PDF
 │
 ├── PDF Analyzer (per-page classification)
 │       ├── Tables / Large images → Docling
 │       └── Standard text pages  → PyMuPDF
 │
 ├── Adaptive Chunking (parser-aware splits)
 │
 ├── Parser Processing (Docling / PyMuPDF per chunk)
 │
 ├── Image Extraction
 │
 ├── Image Filter (size, aspect ratio, solid colour)
 │
 ├── VLM Image Analysis (Qwen2.5-VL via Ollama)
 │       ├── Category classification
 │       ├── Text extraction
 │       └── Description generation
 │
 ├── Markdown Merge (embed image analysis into markdown)
 │
 └── Final Markdown Output
```

### DOC / DOCX Pipeline

```
DOC ──→ LibreOffice Headless ──→ DOCX
                                   │
DOCX ──────────────────────────────┘
 │
 ├── Docling Parser
 ├── Image Extraction & Analysis
 ├── Markdown Merge
 └── Final Markdown Output
```

---

## 📋 Prerequisites

| Requirement | Purpose |
|---|---|
| **Python 3.11+** | Runtime |
| **Ollama** | Hosts the VLM model locally |
| **Qwen2.5-VL:3b** | Vision-Language Model for image analysis |
| **LibreOffice** | DOC → DOCX conversion (headless mode) |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/va1shnav-m/Doc-To-Markdown.git
cd Doc-To-Markdown
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Ollama

Install [Ollama](https://ollama.ai/) and pull the required model:

```bash
ollama pull qwen2.5vl:3b
```

### 5. Run

```bash
python main.py convert ./input --out ./output
```

---

## 💻 Usage

### CLI

```bash
# Convert a single file
python main.py convert document.pdf --out ./output

# Convert multiple files
python main.py convert file1.pdf file2.docx --out ./output

# Convert all documents in a folder
python main.py convert ./input --out ./output

# Use the Docling-only pipeline
python main.py convert ./input --out ./output --pipeline docling

# Skip image analysis
python main.py convert ./input --out ./output --no-analysis

# Overwrite existing output
python main.py convert ./input --out ./output --force
```

### CLI Options

| Option | Default | Description |
|---|---|---|
| `inputs` | *(required)* | One or more input files or folders |
| `--out` | *(required)* | Output folder for generated Markdown |
| `--pipeline` | `hybrid` | Processing pipeline: `hybrid` or `docling` |
| `--no-analysis` | `false` | Skip image analysis |
| `--force` | `false` | Overwrite existing output |

---

## 🐳 Docker

### Build and run with Docker Compose

```bash
docker compose up --build
```

This starts the application on port **8501**.

### Build manually

```bash
docker build -t doc-to-markdown .
docker run -p 8501:8501 doc-to-markdown
```

---

## 📁 Project Structure

```
Doc-To-Markdown/
├── main.py                  # CLI entry point
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container image definition
├── compose.yml              # Docker Compose configuration
│
├── pipelines/
│   ├── hybrid_pipeline.py   # Hybrid (Docling + PyMuPDF) pipeline
│   └── docling_pipeline.py  # Docling-only pipeline
│
├── modules/
│   ├── pdf_analyzer.py      # Per-page analysis & parser selection
│   ├── adaptive_chunker.py  # Parser-aware PDF chunking
│   ├── docling_parser.py    # Docling-based document parser
│   ├── pymupdf_parser.py    # PyMuPDF-based document parser
│   ├── document_chunker.py  # Fixed-size PDF chunker
│   ├── document_processor.py# Document processing utilities
│   ├── doc_converter.py     # DOC → DOCX via LibreOffice
│   ├── image_analyzer.py    # VLM-based image analysis
│   ├── image_filter.py      # Image quality & size filter
│   ├── rapidocr_parser.py   # RapidOCR text extraction
│   ├── smolvlm_caption.py   # SmolVLM caption generation
│   ├── ollama_utils.py      # Ollama health check & startup
│   ├── markdown_merge.py    # Merge image analysis into markdown
│   ├── markdown_combiner.py # Combine chunk markdowns
│   ├── reporting.py         # Processing report generation
│   ├── ui.py                # Console UI helpers
│   └── utils.py             # General utilities
│
├── benchmark/
│   ├── benchmark.py         # Benchmark data model
│   └── report_generator.py  # HTML benchmark report generator
│
├── docs/
│   └── deployment.md        # Deployment guide
│
└── .github/
    └── workflows/
        └── ci.yml           # GitHub Actions CI pipeline
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **Document Parsing** | [Docling](https://github.com/DS4SD/docling) | Complex pages (tables, images, layouts) |
| **PDF Parsing** | [PyMuPDF](https://pymupdf.readthedocs.io/) | Fast text-only page extraction |
| **OCR** | [RapidOCR](https://github.com/RapidAI/RapidOCR) | Optical character recognition for images |
| **Image Analysis** | [Qwen2.5-VL](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct) via [Ollama](https://ollama.ai/) | VLM-based image classification & description |
| **Image Processing** | [Pillow](https://python-pillow.org/) | Image resizing and manipulation |
| **Perceptual Hashing** | [ImageHash](https://github.com/JohannesBuchner/imagehash) | Duplicate image detection |
| **DOC Conversion** | LibreOffice (Headless) | `.doc` → `.docx` conversion |
| **Containerization** | Docker + Docker Compose | Deployment |

---

## ⚙️ CI/CD

The project uses **GitHub Actions** for continuous integration:

- ✅ Python syntax validation (`compileall`)
- ✅ Dependency installation check
- ✅ Docker image build verification

Triggers on pushes and pull requests to `main`.

---

## 📊 Benchmark Reports

Each document conversion generates an HTML benchmark report containing:

- **Document metadata** — Name, type, file size
- **Stage-level timings** — Analysis, chunking, parsing, image analysis, markdown merge
- **Image processing stats** — Detected, analyzed, cached, skipped, failed
- **Per-image analysis times**

Reports are saved alongside the output markdown in the output directory.

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

---

## 📝 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ by [va1shnav-m](https://github.com/va1shnav-m)

</div>
]]>
