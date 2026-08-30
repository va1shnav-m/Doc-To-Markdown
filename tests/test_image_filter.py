"""Unit tests for image filtering logic."""

import tempfile
import unittest
from pathlib import Path
from PIL import Image

from modules.image_filter import should_process


class TestImageFilter(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_image(self, filename, size, color="white"):
        img_path = self.dir_path / filename
        img = Image.new("RGB", size, color=color)
        img.save(img_path)
        return img_path

    def _create_multi_color_image(self, filename, size):
        img_path = self.dir_path / filename
        img = Image.new("RGB", size, color="white")
        # Draw a black line to ensure it is not solid color
        for x in range(min(size[0], 50)):
            img.putpixel((x, 0), (0, 0, 0))
        img.save(img_path)
        return img_path

    def test_tiny_image_skipped(self):
        img_path = self._create_multi_color_image("tiny.png", (100, 100))
        self.assertFalse(should_process(img_path))

    def test_narrow_side_skipped(self):
        img_path = self._create_multi_color_image("narrow.png", (300, 20))
        self.assertFalse(should_process(img_path))

    def test_extreme_aspect_ratio_skipped(self):
        img_path = self._create_multi_color_image("aspect.png", (800, 40))
        self.assertFalse(should_process(img_path))

    def test_solid_color_skipped(self):
        img_path = self._create_image("solid.png", (400, 400), color="blue")
        self.assertFalse(should_process(img_path))

    def test_valid_image_accepted(self):
        img_path = self._create_multi_color_image("valid.png", (500, 400))
        self.assertTrue(should_process(img_path))


if __name__ == "__main__":
    unittest.main()

