from pathlib import Path
import json
import tempfile
import time

import imagehash
import ollama
from PIL import Image

from modules.image_filter import should_process
from modules.ollama_utils import ensure_ollama_running

# ------------------------------------
# Configuration
# ------------------------------------

CACHE_FILE = Path("image_analysis_cache.json")

MAX_IMAGE_SIZE = 1024

PHASH_THRESHOLD = 4

MODEL = "qwen2.5vl:3b"

# ------------------------------------
# Prompt
# ------------------------------------

ANALYSIS_PROMPT = """
You are a document image analyzer for a technical document parsing system.

Analyze the image and produce TWO sections of output.

STEP 1: Classify the image as ONE of:
- technical: The image has meaningful text content, blocks, connectors, labels, tables, charts, diagrams, flowcharts, architecture, code, UI elements, or any structured information.
- general: The image is a photo, illustration, icon, logo, decorative element, or has no meaningful text or structure.

STEP 2: Produce output in this EXACT format:

**Category:** [technical or general]

## Text Extract

[For TECHNICAL images:]
- Extract ALL visible text from the image
- Preserve the spatial layout and relationships between text elements
- If there are blocks/boxes with text, show them as bullet points or sections
- If there are arrows or connectors between blocks, show them using → notation
- If there is a table, reproduce it as a markdown table
- If there is a hierarchy or grouping, use indentation to show it
- The goal is to convert the visual text layout into meaningful structured markdown

[For GENERAL images:]
- Write: No text content.

## Description

[For TECHNICAL images:]
- Explain what this image represents and its purpose
- Describe the key concepts, relationships, or processes shown
- If it shows a system architecture, explain what the system does
- If it shows a process, explain the flow
- If it shows data, explain what the data means
- Adapt the depth of description to the complexity of the image

[For GENERAL images:]
- Provide a brief 1-2 sentence description of what is visible

IMPORTANT RULES:
- Do NOT invent information that is not clearly visible
- Do NOT add conversational text like "Here is..." or "I can see..."
- Preserve ALL visible text labels exactly as written
- The Text Extract section should capture EVERY piece of text in the image
- The Description section should explain the MEANING and CONTEXT
"""

# ------------------------------------
# Cache
# ------------------------------------


def load_cache():

    if CACHE_FILE.exists():

        with open(CACHE_FILE, "r", encoding="utf-8") as f:

            return json.load(f)

    return {}


def save_cache(cache):

    with open(CACHE_FILE, "w", encoding="utf-8") as f:

        json.dump(cache, f, indent=4, ensure_ascii=False)


# ------------------------------------
# Perceptual Hash
# ------------------------------------


def image_hash(image_path):

    return imagehash.phash(Image.open(image_path))


def find_similar_hash(current_hash, cache):

    for cached_hash in cache.keys():

        cached = imagehash.hex_to_hash(cached_hash)

        distance = current_hash - cached

        if distance <= PHASH_THRESHOLD:

            return cached_hash

    return None


# ------------------------------------
# Resize
# ------------------------------------


def resize_image(image_path):

    img = Image.open(image_path)

    img.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))

    temp = tempfile.NamedTemporaryFile(
        suffix=".png",
        delete=False
    )

    img.save(temp.name)

    return temp.name


# ------------------------------------
# Parse VLM Response
# ------------------------------------


def parse_analysis_response(response_text):
    """
    Parse the VLM response into category, text extract,
    and description.

    Returns
    -------
    dict
        {
            "category": "technical" or "general",
            "text_extract": str,
            "description": str,
        }
    """

    text = response_text.strip()

    category = "general"
    text_extract = ""
    description = ""

    # ------------------------------------------
    # Extract category from **Category:** line
    # ------------------------------------------

    lines = text.splitlines()

    for line in lines:

        stripped = line.strip().lower()

        if stripped.startswith("**category:**"):

            value = stripped.split(":", 1)[1]
            value = value.strip().strip("*").strip()

            if "technical" in value:
                category = "technical"
            else:
                category = "general"

            break

    # ------------------------------------------
    # Extract sections by heading
    # ------------------------------------------

    current_section = None
    text_extract_lines = []
    description_lines = []

    for line in lines:

        stripped = line.strip().lower()

        # Detect section headers
        if stripped.startswith("## text extract"):
            current_section = "text_extract"
            continue

        elif stripped.startswith("## description"):
            current_section = "description"
            continue

        # Skip the category line
        elif stripped.startswith("**category:**"):
            continue

        # Collect content into sections
        if current_section == "text_extract":
            text_extract_lines.append(line)

        elif current_section == "description":
            description_lines.append(line)

    text_extract = "\n".join(text_extract_lines).strip()
    description = "\n".join(description_lines).strip()

    return {
        "category": category,
        "text_extract": text_extract,
        "description": description,
    }


# ------------------------------------
# Image Analyzer
# ------------------------------------


def analyze_images(assets_dir):
    """
    Analyze all images inside assets folder using a VLM.

    Classifies each image and produces structured markdown
    that preserves relationships for technical images.

    Parameters
    ----------
    assets_dir : str | Path

    Returns
    -------
    dict
        {
            "results": {
                "image_1.png": {
                    "category": "technical",
                    "text_extract": "...",
                    "description": "..."
                },
                ...
            },
            "generated": int,
            "cached": int,
            "skipped": int,
            "failed": int,
            "analysis_times": {
                "image_1.png": 3.21,
                ...
            }
        }
    """

    assets_dir = Path(assets_dir)

    cache = load_cache()

    results = {}
    analysis_times = {}

    image_files = sorted(
        [
            *assets_dir.glob("*.png"),
            *assets_dir.glob("*.jpg"),
            *assets_dir.glob("*.jpeg"),
            *assets_dir.glob("*.webp"),
        ]
    )

    total_start = time.perf_counter()

    skipped = 0
    cached = 0
    generated = 0
    failed = 0

    if not ensure_ollama_running():
        raise RuntimeError(
            "Ollama could not be started. "
            "Please make sure Ollama is installed correctly."
        )

    for image_path in image_files:

        image_start = time.perf_counter()

        # ------------------------------------
        # Image Filter
        # ------------------------------------

        if not should_process(image_path):
            skipped += 1
            continue

        # ------------------------------------
        # pHash Cache
        # ------------------------------------

        current_hash = image_hash(image_path)

        similar_hash = find_similar_hash(
            current_hash,
            cache
        )

        if similar_hash is not None:

            cached += 1

            results[image_path.name] = cache[similar_hash]

            print(
                f"Using cached analysis for {image_path.name}"
            )

            continue

        # ------------------------------------
        # Resize
        # ------------------------------------

        resized = resize_image(image_path)

        # ------------------------------------
        # VLM Analysis
        # ------------------------------------

        try:

            response = ollama.chat(

                model=MODEL,

                messages=[
                    {
                        "role": "user",
                        "content": ANALYSIS_PROMPT,
                        "images": [resized]
                    }
                ],

                options={
                    "temperature": 0,
                    "top_p": 0.9,
                    "repeat_penalty": 1.05,
                    "num_predict": 800,
                }
            )

        except Exception as e:

            failed += 1

            print(
                f"Analysis failed for {image_path.name}: {e}"
            )

            # Store a failed marker so merge can still embed the image
            results[image_path.name] = {
                "category": "general",
                "text_extract": "",
                "description": "",
                "failed": True,
            }

            continue

        raw_response = response["message"]["content"].strip()

        parsed = parse_analysis_response(raw_response)

        results[image_path.name] = parsed

        cache[str(current_hash)] = parsed

        generated += 1

        image_end = time.perf_counter()
        analysis_time = image_end - image_start
        analysis_times[image_path.name] = analysis_time

        print(
            f"{image_path.name} [{parsed['category']}] "
            f"analyzed in {analysis_time:.2f} seconds"
        )

    save_cache(cache)

    total_end = time.perf_counter()

    print("\n==============================")
    print("Image Analysis Summary")
    print("==============================")
    print(f"Total Images     : {len(image_files)}")
    print(f"Analyzed         : {generated}")
    print(f"Cached           : {cached}")
    print(f"Skipped          : {skipped}")
    print(f"Failed           : {failed}")
    print(f"Total Time       : {total_end-total_start:.2f} sec")
    print("==============================")

    return {
        "results": results,
        "generated": generated,
        "cached": cached,
        "skipped": skipped,
        "failed": failed,
        "analysis_times": analysis_times,
    }
