"""Unit tests for markdown combiner utilities."""

import tempfile
import unittest
from pathlib import Path

from modules.markdown_combiner import combine_markdowns, combine_final_documents


class TestMarkdownCombiner(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_combine_markdowns(self):
        (self.dir_path / "chunk_0001.md").write_text("# Chunk 1", encoding="utf-8")
        (self.dir_path / "chunk_0002.md").write_text("Chunk 2 text", encoding="utf-8")

        output_file = combine_markdowns(self.dir_path, output_name="combined.md")
        self.assertTrue(output_file.exists())
        content = output_file.read_text(encoding="utf-8")
        self.assertIn("# Chunk 1", content)
        self.assertIn("Chunk 2 text", content)

    def test_combine_final_documents_skips_raw(self):
        (self.dir_path / "document_0001.md").write_text("# Doc 1", encoding="utf-8")
        (self.dir_path / "document_0001_raw.md").write_text("# Raw intermediate", encoding="utf-8")
        (self.dir_path / "document_0002.md").write_text("# Doc 2", encoding="utf-8")

        final_output = combine_final_documents(self.dir_path)
        self.assertTrue(final_output.exists())
        content = final_output.read_text(encoding="utf-8")
        self.assertIn("# Doc 1", content)
        self.assertIn("# Doc 2", content)
        self.assertNotIn("# Raw intermediate", content)


if __name__ == "__main__":
    unittest.main()

