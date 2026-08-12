from .benchmark import Benchmark


def generate_benchmark_report(benchmark: Benchmark) -> str:
    """
    Generate an HTML benchmark report for one document.
    """

    caption_times = list(benchmark.caption_times.values())

    if caption_times:
        caption_avg = sum(caption_times) / len(caption_times)
        caption_min = min(caption_times)
        caption_max = max(caption_times)
    else:
        caption_avg = 0
        caption_min = 0
        caption_max = 0

    stage_percentages = {}

    if benchmark.total_time > 0:
        for stage, duration in benchmark.stage_times.items():
            stage_percentages[stage] = (
                duration / benchmark.total_time
            ) * 100

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Document Processing Benchmark</title>
    </head>

    <body>

        <h1>Document Processing Benchmark</h1>

        <h2>Document Information</h2>

        <p><strong>Document:</strong> {benchmark.document_name}</p>
        <p><strong>Type:</strong> {benchmark.document_type}</p>
        <p><strong>File Size:</strong> {benchmark.file_size_mb:.2f} MB</p>

        <h2>Performance</h2>

        <p>
            <strong>Total Processing Time:</strong>
            {benchmark.total_time:.2f} seconds
        </p>

        <h2>Pipeline Stage Timing</h2>

        <table border="1" cellpadding="6" cellspacing="0">
            <tr>
                <th>Stage</th>
                <th>Time (seconds)</th>
            </tr>

            {
                "".join(
                    f"""
                    <tr>
                        <td>{stage.replace("_", " ").title()}</td>
                        <td>{duration:.2f}</td>
                    </tr>
                    """
                    for stage, duration in benchmark.stage_times.items()
                )
            }

        </table>

        <h2>Image Statistics</h2>

        <table border="1" cellpadding="6" cellspacing="0">
            <tr>
                <th>Metric</th>
                <th>Count</th>
            </tr>

            <tr>
                <td>Images Detected</td>
                <td>{benchmark.images_detected}</td>
            </tr>

            <tr>
                <td>Images Processed</td>
                <td>{benchmark.images_processed}</td>
            </tr>

            <tr>
                <td>Images Skipped</td>
                <td>{benchmark.images_skipped}</td>
            </tr>
        </table>

        <h2>OCR Statistics</h2>

        <table border="1" cellpadding="6" cellspacing="0">
            <tr>
                <th>Metric</th>
                <th>Count</th>
            </tr>

            <tr>
                <td>Images Processed by OCR</td>
                <td>{benchmark.ocr_images}</td>
            </tr>

            <tr>
                <td>OCR Cache Hits</td>
                <td>{benchmark.ocr_cache_hits}</td>
            </tr>

            <tr>
                <td>Images Skipped</td>
                <td>{benchmark.images_skipped}</td>
            </tr>

            <tr>
                <td>OCR Failures</td>
                <td>{benchmark.ocr_failed}</td>
            </tr>

            <tr>
                <td>Characters Extracted</td>
                <td>{benchmark.ocr_characters:,}</td>
            </tr>
        </table>

        <h2>Captioning Statistics</h2>

        <table border="1" cellpadding="6" cellspacing="0">
            <tr>
                <th>Metric</th>
                <th>Count</th>
            </tr>

            <tr>
                <td>Images Requiring Captioning</td>
                <td>{benchmark.caption_images}</td>
            </tr>

            <tr>
                <td>Captions Generated</td>
                <td>{benchmark.caption_success}</td>
            </tr>

            <tr>
                <td>Captions from Cache</td>
                <td>{benchmark.caption_cache_hits}</td>
            </tr>

            <tr>
                <td>Captions Skipped</td>
                <td>{benchmark.caption_skipped}</td>
            </tr>

            <tr>
                <td>Caption Failures</td>
                <td>{benchmark.caption_failed}</td>
            </tr>
        </table>

        <h2>Per-Image Caption Timing</h2>

        <table border="1" cellpadding="6" cellspacing="0">
            <tr>
                <th>Image</th>
                <th>Caption Time (seconds)</th>
            </tr>

            {
                "".join(
                    f"""
                    <tr>
                        <td>{image_name}</td>
                        <td>{duration:.2f}</td>
                    </tr>
                    """
                    for image_name, duration
                    in benchmark.caption_times.items()
                )
            }

        </table>

        <h2>Caption Timing Summary</h2>

        <table border="1" cellpadding="6" cellspacing="0">
            <tr>
                <th>Metric</th>
                <th>Time (seconds)</th>
            </tr>

            <tr>
                <td>Average Caption Time</td>
                <td>{caption_avg:.2f}</td>
            </tr>

            <tr>
                <td>Fastest Caption</td>
                <td>{caption_min:.2f}</td>
            </tr>

            <tr>
                <td>Slowest Caption</td>
                <td>{caption_max:.2f}</td>
            </tr>
        </table>

        <h2>Pipeline Time Distribution</h2>

        <table border="1" cellpadding="6" cellspacing="0">
            <tr>
                <th>Stage</th>
                <th>Time (seconds)</th>
                <th>Percentage of Total</th>
            </tr>

            {
                "".join(
                    f"""
                    <tr>
                        <td>{stage.replace("_", " ").title()}</td>
                        <td>{duration:.2f}</td>
                        <td>{stage_percentages.get(stage, 0):.2f}%</td>
                    </tr>
                    """
                    for stage, duration in benchmark.stage_times.items()
                )
            }

        </table>

        <h2>Errors and Failures</h2>

        {
            (
                "<p>No errors reported.</p>"
                if not benchmark.errors
                else
                """
                <ul>
                """
                + "".join(
                    f"<li>{error}</li>"
                    for error in benchmark.errors
                )
                + """
                </ul>
                """
            )
        }


    </body>
    </html>
    """

