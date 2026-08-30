"""Unit tests for benchmark metrics and HTML report generation."""

import unittest
from benchmark.benchmark import Benchmark
from benchmark.report_generator import generate_benchmark_report


class TestBenchmark(unittest.TestCase):

    def test_benchmark_initialization(self):
        b = Benchmark()
        self.assertEqual(b.total_time, 0.0)
        self.assertEqual(b.images_detected, 0)
        self.assertEqual(len(b.errors), 0)

        b.errors.append("Sample error")
        self.assertEqual(len(b.errors), 1)

    def test_generate_benchmark_report_html(self):
        b = Benchmark(
            document_name="sample.pdf",
            document_type=".pdf",
            file_size_mb=1.5,
            total_pages=5,
            total_time=12.34,
            pymupdf_pages=3,
            docling_pages=2,
            images_detected=4,
            images_processed=4,
            images_analyzed=3,
            images_cached=1,
            images_skipped=0,
            images_failed=0,
            stage_times={
                "analysis": 1.0,
                "chunking": 0.5,
                "parsing": 5.0,
                "image_analysis": 4.5,
                "markdown_merge": 1.34,
            },
            analysis_times={
                "img_1.png": 2.2,
                "img_2.png": 2.3,
            },
        )

        html = generate_benchmark_report(b)
        self.assertIsInstance(html, str)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("sample.pdf", html)
        self.assertIn("12.34", html)
        self.assertIn("img_1.png", html)


if __name__ == "__main__":
    unittest.main()
