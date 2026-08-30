"""Unit tests for adaptive chunker logic."""

import unittest
from modules.adaptive_chunker import create_execution_plan
from modules.config import MAX_CHUNK_SIZE, MAX_DOCLING_CHUNK_SIZE


class TestAdaptiveChunker(unittest.TestCase):

    def test_empty_analysis(self):
        plan = create_execution_plan([])
        self.assertEqual(plan, [])

    def test_single_page(self):
        analysis = [{"page": 1, "parser": "pymupdf"}]
        plan = create_execution_plan(analysis)
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]["parser"], "pymupdf")
        self.assertEqual(plan[0]["start_page"], 1)
        self.assertEqual(plan[0]["end_page"], 1)
        self.assertEqual(plan[0]["page_count"], 1)

    def test_pymupdf_chunk_limit(self):
        # Generate 15 consecutive pymupdf pages
        analysis = [
            {"page": i, "parser": "pymupdf"}
            for i in range(1, 16)
        ]
        plan = create_execution_plan(analysis)
        # Should split into chunks of at most MAX_CHUNK_SIZE (10)
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0]["page_count"], MAX_CHUNK_SIZE)
        self.assertEqual(plan[0]["start_page"], 1)
        self.assertEqual(plan[0]["end_page"], 10)
        self.assertEqual(plan[1]["page_count"], 5)
        self.assertEqual(plan[1]["start_page"], 11)
        self.assertEqual(plan[1]["end_page"], 15)

    def test_docling_chunk_limit(self):
        # Generate 12 consecutive docling pages
        analysis = [
            {"page": i, "parser": "docling"}
            for i in range(1, 13)
        ]
        plan = create_execution_plan(analysis)
        # Should split into chunks of at most MAX_DOCLING_CHUNK_SIZE (5)
        self.assertEqual(len(plan), 3)
        self.assertEqual(plan[0]["page_count"], MAX_DOCLING_CHUNK_SIZE)
        self.assertEqual(plan[1]["page_count"], MAX_DOCLING_CHUNK_SIZE)
        self.assertEqual(plan[2]["page_count"], 2)

    def test_alternating_parsers(self):
        analysis = [
            {"page": 1, "parser": "pymupdf"},
            {"page": 2, "parser": "docling"},
            {"page": 3, "parser": "pymupdf"},
        ]
        plan = create_execution_plan(analysis)
        self.assertEqual(len(plan), 3)
        self.assertEqual(plan[0]["parser"], "pymupdf")
        self.assertEqual(plan[1]["parser"], "docling")
        self.assertEqual(plan[2]["parser"], "pymupdf")


if __name__ == "__main__":
    unittest.main()

