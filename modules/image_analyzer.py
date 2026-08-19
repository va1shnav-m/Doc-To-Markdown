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

Analyze the image and produce structured markdown output.

STEP 1: Classify the image as ONE of these types:
- diagram (system design, architecture, component diagrams)
- flowchart (process flows, decision trees, sequence diagrams)
- table (data tables, comparison matrices)
- chart (bar charts, pie charts, line graphs, plots)
- screenshot (UI screenshots, terminal output, code snippets)
- photo (photographs, real-world images)
- illustration (icons, logos, decorative art)
- other

STEP 2: Produce output based on the type.

FOR DIAGRAMS AND ARCHITECTURE:
- List all visible components/nodes with their labels
- Describe all connections between components using arrows (→)
- Preserve grouping and hierarchy (e.g. components inside a boundary)
- Include any text labels on connections or arrows
- Format as structured markdown with headers and bullet lists

FOR FLOWCHARTS AND PROCESS FLOWS:
- List each step/node in order
- Show the flow direction with arrows (→)
- Include decision points with their conditions
- Show branches clearly

FOR TABLES:
- Reproduce the table as a markdown table
- Preserve all headers and cell values

FOR CHARTS:
- Describe the chart type
- List the axes labels and data series
- Mention key data points or trends that are clearly visible
- Do NOT invent values that are not readable

FOR SCREENSHOTS AND UI:
- Describe the application or interface shown
- List key visible content, menus, or data
- Include any important visible text

FOR PHOTOS, ILLUSTRATIONS, AND OTHER:
- Provide a 1-2 sentence description of what is visible

OUTPUT FORMAT (always start with this exact line):

**Type:** [type]

[structured content based on the type above]

IMPORTANT RULES:
- Do NOT invent information that is not clearly visible
- Do NOT describe colors or visual styling unless they convey meaning
- Do NOT add conversational text like "Here is..." or "I can see..."
- Preserve ALL visible text labels exactly as written
- For technical diagrams, RELATIONSHIPS are more important than descriptions
- Keep your response concise and structured
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
    Parse the VLM response into type and markdown content.

    Returns
    -------
    dict
        {"type": str, "markdown": str}
    """

    text = response_text.strip()

    image_type = "other"
    markdown = text

    # Extract type from the **Type:** line
    for line in text.splitlines():

        stripped = line.strip()

        if stripped.lower().startswith("**type:**"):

            type_value = stripped.split(":", 1)[1]
            type_value = type_value.strip().strip("*").strip().lower()

            # Normalize to known types
            known_types = [
                "diagram", "flowchart", "table",
                "chart", "screenshot", "photo",
                "illustration", "other",
            ]

            for known in known_types:
                if known in type_value:
                    image_type = known
                    break

            # Remove the Type line from markdown
            markdown = text.replace(line, "", 1).strip()

            break

    return {
        "type": image_type,
        "markdown": markdown,
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
                    "type": "diagram",
                    "markdown": "..."
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
                    "num_predict": 512,
                }
            )

        except Exception as e:

            failed += 1

            print(
                f"Analysis failed for {image_path.name}: {e}"
            )

            # Store a failed marker so merge can still embed the image
            results[image_path.name] = {
                "type": "other",
                "markdown": "",
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
            f"{image_path.name} [{parsed['type']}] "
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
