# Deployment Guide

## Project Overview

This application converts PDF, DOC, and DOCX files into Markdown while preserving document structure for Retrieval-Augmented Generation (RAG) workflows. It extracts text, images, and tables, generates image captions using a local vision-language model, and produces a single merged Markdown document.

---

## Processing Workflow

### PDF

```
PDF
│
├── PDF Analyzer
│
├── Docling (complex pages)
│
└── PyMuPDF (standard pages)
      │
      ▼
Markdown Chunks
      │
      ▼
Image Extraction
      │
      ▼
Image Filter
      │
      ▼
RapidOCR
      │
      ▼
SmolVLM (via Ollama)
      │
      ▼
Markdown Merge
      │
      ▼
Final Markdown
```

### DOC

```
DOC
│
▼
LibreOffice (Headless)
│
▼
DOCX
│
▼
Docling
│
▼
Image Extraction
│
▼
RapidOCR
│
▼
SmolVLM (via Ollama)
│
▼
Markdown Merge
│
▼
Final Markdown
```

### DOCX

```
DOCX
│
▼
Docling
│
▼
Image Extraction
│
▼
RapidOCR
│
▼
SmolVLM (via Ollama)
│
▼
Markdown Merge
│
▼
Final Markdown
```

---

## Runtime Components

| Component | Purpose |
|----------|---------|
| Streamlit | Web interface |
| Docling | Document parsing |
| PyMuPDF | PDF parsing |
| RapidOCR | OCR for extracted images |
| SmolVLM | Image caption generation |
| LibreOffice Headless | DOC → DOCX conversion |
| Ollama | Hosts the SmolVLM model |

---

## Runtime Directories

| Directory | Purpose |
|----------|---------|
| `assets/` | Extracted images |
| `output/` | Final Markdown output |
| `temp/` | Temporary files |
| `temp_chunks/` | Temporary PDF chunks |
| `caption_cache.json` | Stores generated image captions |

Temporary directories are automatically cleaned when a new document is processed.

---

## External Dependencies

- Python
- LibreOffice Headless
- Ollama
- SmolVLM model

---

## Current Limitations

- Image caption generation depends on the Ollama service.
- The application currently supports a single user.
- The project has not yet been containerized.

---

## Planned Deployment

The target deployment architecture is:

- Docker
- Docker Compose
- Separate containers for:
  - Application
  - Ollama