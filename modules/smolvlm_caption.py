from pathlib import Path
import json
import tempfile
import time

import imagehash
import ollama
from PIL import Image

from modules.image_filter import should_caption

# ------------------------------------
# Configuration
# ------------------------------------

CACHE_FILE = Path("caption_cache.json")

MAX_IMAGE_SIZE = 512

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
Describe this image in 1-2 concise sentences.

Focus only on technical content:
- diagrams
- flowcharts
- architecture
- UI/screenshots
- tables
- graphs
- code
- forms

Mention only the purpose and key components.

Ignore colors, styling, decorations, logos, icons, and blank images.

If there is no meaningful technical content, respond exactly:
SKIP"""

    assets_dir = Path(assets_dir)

    cache = load_cache()

    captions = {}

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

        if not should_caption(image_path):
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

        response = ollama.chat(

            #model="qwen2.5vl:3b",
            model="ahmadwaqar/smolvlm2-2.2b-instruct:latest",

            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [resized]
                }
            ],

            options = {
                "temperature": 0,
                
                "repeat_penalty": 1.1,
            }

        )

        caption = response["message"]["content"].strip()

        captions[image_path.name] = caption

        cache[str(current_hash)] = caption

        generated += 1

        image_end = time.perf_counter()

        print(
            f"{image_path.name} generated in "
            f"{image_end-image_start:.2f} seconds"
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

    return captions