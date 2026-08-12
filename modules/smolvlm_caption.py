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

CACHE_FILE = Path("caption_cache.json")

MAX_IMAGE_SIZE = 1024

PHASH_THRESHOLD = 4

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

        json.dump(cache, f, indent=4)


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
# Caption Generator
# ------------------------------------


def generate_captions(assets_dir, ocr_results):

    prompt = """
You are an image captioning component in a document parsing system.

Describe ONLY what is clearly visible in the image in 1-2 concise sentences.

First identify the type of visual content when possible:
photograph, diagram, chart, table, screenshot, technical figure, or illustration.

Focus on:
- the main purpose or subject of the image
- important technical information
- diagrams, charts, workflows, or relationships
- important visible text when it helps identify the content

For diagrams and technical figures:
- identify the overall subject or purpose
- mention important entities, labels, components, or sections
- describe major relationships or flow only when clearly visible
- use visible text as evidence for understanding the figure

For screenshots or interfaces:
- describe the application/interface and the important visible content

For charts:
- describe the chart type and the main information shown
- do not invent numerical values or trends that are not clearly visible

For photographs or illustrations:
- describe the main visible subjects and actions

IMPORTANT:
- Do not infer a scene from individual words.
- Do not invent objects, people, locations, actions, or events.
- Do not turn technical diagrams into real-world scenes.
- If the image is a database/schema diagram, describe it as a database/schema diagram.
- If the content is unclear, give a conservative description rather than guessing.
- Do not describe colors, style, or appearance unless important.

Return ONLY the caption.
"""


#     prompt = """
# You are an image captioning component in a document parsing system.

# Describe ONLY what is clearly visible in the image in 1-2 concise sentences.

# Identify the type of visual when possible, such as a photograph,
# diagram, chart, table, screenshot, or technical figure.

# For diagrams and technical figures, describe the overall subject,
# main components, and visible relationships.

# Use the visual structure of the image as the primary source of truth.
# Do not infer a real-world scene from individual words or labels.

# Do not invent objects, people, actions, locations, or information
# that are not clearly visible.

# If the image is unclear or difficult to interpret, give a
# conservative description rather than guessing.

# Return ONLY the caption.
# """

#     prompt = """
# You are an image captioning component in a document parsing system.

# Describe the content of the image in 1-2 concise sentences.

# Focus on:
# - the main purpose or subject of the image
# - important technical information
# - diagrams, charts, workflows, or screenshots
# - important visible text when it helps explain the content

# If the image contains a diagram or process, describe what it represents
# and the main relationships or flow shown.

# If the image contains text, summarize the meaningful information rather
# than trying to reproduce all the text.

# Do not invent or infer information that is not clearly visible.
# Do not describe colors, style, or appearance unless it is important.
# Return only the caption.
# """


    # prompt = """
    # Describe this document image in 1-2 concise sentences.

    # Focus on:
    # - the main subject or purpose of the image
    # - important technical content
    # - diagrams, charts, or workflows
    # - visible text when it is important to understanding the image

    # Do not guess information that is not visible.
    # Do not describe colors or visual appearance unless relevant.
    # Return only the caption."""

#     prompt = """
# You are an image captioning engine for document parsing.

# Describe the visible technical content in 1-2 concise sentences.

# Describe only what is visible.
# Do not infer, explain, speculate, ask questions, offer help, mention missing context, or use conversational language.

# If there is no meaningful technical content, reply exactly:
# SKIP
# """

    assets_dir = Path(assets_dir)

    cache = load_cache()

    captions = {}
    caption_times = {}
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

        ocr_info = ocr_results.get(
            image_path.name,
            {
                "text": "",
                "char_count": 0,
                "line_count": 0
            }
        )

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

            captions[image_path.name] = cache[similar_hash]

            print(
                f"Using cached caption for {image_path.name}"
            )

            continue

        # ------------------------------------
        # Resize
        # ------------------------------------

        resized = resize_image(image_path)

        # ------------------------------------
        # SmolVLM
        # ------------------------------------

        try:

            response = ollama.chat(

                #model="qwen2.5vl:3b",
                # model="ahmadwaqar/smolvlm2-2.2b-instruct:latest",
                # model="richardyoung/smolvlm2-2.2b-instruct:q4_k_m",
                model="ahmadwaqar/smolvlm2-500m-video",

                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [resized]
                    }
                ],

                options={
                    "temperature": 0,
                    "top_p": 0.9,
                    "repeat_penalty": 1.2,
                    "num_predict": 150,
                }
            )

        except Exception as e:

            failed += 1

            print(
                f"Caption failed for {image_path.name}: {e}"
            )

            continue

        caption = response["message"]["content"].strip()

        captions[image_path.name] = caption

        cache[str(current_hash)] = caption

        generated += 1

        image_end = time.perf_counter()
        caption_time = image_end - image_start
        caption_times[image_path.name] = caption_time
        print(
            f"{image_path.name} generated in "
            f"{caption_time:.2f} seconds"
        )

    save_cache(cache)

    total_end = time.perf_counter()

    print("\n==============================")
    print("Caption Generation Summary")
    print("==============================")
    print(f"Total Images     : {len(image_files)}")
    print(f"Generated        : {generated}")
    print(f"Cached           : {cached}")
    print(f"Skipped          : {skipped}")
    print(f"Total Time       : {total_end-total_start:.2f} sec")
    print("==============================")

    return {
        "captions": captions,
        "generated": generated,
        "cached": cached,
        "skipped": skipped,
        "failed": failed,
        "caption_times": caption_times,
    }