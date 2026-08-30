"""
Configuration constants and environment settings for Doc-To-Markdown.
All values have sensible defaults and can be overridden via environment variables.
"""

import os
from pathlib import Path

# ---------------------------------------------------------
# Vision Language Model (VLM) & Ollama
# ---------------------------------------------------------
VLM_MODEL = os.getenv("VLM_MODEL", "qwen2.5vl:3b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_STARTUP_TIMEOUT = int(os.getenv("OLLAMA_STARTUP_TIMEOUT", "60"))

# ---------------------------------------------------------
# Image Analysis & Deduplication Cache
# ---------------------------------------------------------
IMAGE_ANALYSIS_CACHE_FILE = Path(
    os.getenv("IMAGE_ANALYSIS_CACHE_FILE", "image_analysis_cache.json")
)
MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", "1024"))
PHASH_THRESHOLD = int(os.getenv("PHASH_THRESHOLD", "4"))

# ---------------------------------------------------------
# Image Quality Filter Rules
# ---------------------------------------------------------
MIN_IMAGE_WIDTH = int(os.getenv("MIN_IMAGE_WIDTH", "180"))
MIN_IMAGE_HEIGHT = int(os.getenv("MIN_IMAGE_HEIGHT", "180"))
MIN_IMAGE_SIDE = int(os.getenv("MIN_IMAGE_SIDE", "32"))
MAX_ASPECT_RATIO = float(os.getenv("MAX_ASPECT_RATIO", "15.0"))

# ---------------------------------------------------------
# PDF Layout Analysis & Chunking
# ---------------------------------------------------------
IMAGE_AREA_THRESHOLD = float(os.getenv("IMAGE_AREA_THRESHOLD", "0.10"))
MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", "10"))
MAX_DOCLING_CHUNK_SIZE = int(os.getenv("MAX_DOCLING_CHUNK_SIZE", "5"))
DEFAULT_DOCLING_FIXED_CHUNK_SIZE = int(os.getenv("DOCLING_FIXED_CHUNK_SIZE", "25"))

# ---------------------------------------------------------
# File Formats
# ---------------------------------------------------------
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}

