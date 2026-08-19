import argparse
import time
from pathlib import Path

from modules.ui import ConsoleUI
from modules.doc_converter import convert_doc
from modules.utils import clear_folder
from modules.markdown_combiner import combine_final_documents
from modules.reporting import print_report

from pipelines.hybrid_pipeline import process_hybrid_pipeline
from pipelines.docling_pipeline import process_docling_pipeline

from benchmark.benchmark import Benchmark
from benchmark.report_generator import generate_benchmark_report


def main():

    parser = argparse.ArgumentParser(
        description="Document to Markdown Converter"
    )

    subparsers = parser.add_subparsers(dest="command")

    # -------------------------------------------
    # convert command
    # -------------------------------------------

    convert = subparsers.add_parser(
        "convert",
        help="Convert documents to markdown"
    )

    convert.add_argument(
        "inputs",
        nargs="+",
        help="One or more input folders or file paths"
    )

    convert.add_argument(
        "--out",
        required=True,
        help="Output folder"
    )

    convert.add_argument(
        "--pipeline",
        choices=["hybrid", "docling"],
        default="hybrid",
        help="Processing pipeline (default: hybrid)"
    )

    convert.add_argument(
        "--no-analysis",
        action="store_true",
        help="Skip image analysis"
    )

    convert.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "convert":
        run_convert(args)


def run_convert(args):

    output_folder = Path(args.out)
    ui = ConsoleUI()

    output_folder.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------
    # Collect documents
    # -------------------------------------------

    supported_extensions = {".pdf", ".docx", ".doc"}
    documents = []
    seen_paths = set()

    for path_str in args.inputs:
        input_path = Path(path_str)

        if not input_path.exists():
            print(f"Warning: Input path not found, skipping: {input_path}")
            continue

        if input_path.is_file():
            if input_path.suffix.lower() not in supported_extensions:
                print(f"Warning: Unsupported file type, skipping: {input_path}")
                continue
            resolved_path = input_path.resolve()
            if resolved_path not in seen_paths:
                documents.append(input_path)
                seen_paths.add(resolved_path)
        else:
            files_in_folder = sorted([
                f for f in input_path.rglob("*")
                if f.suffix.lower() in supported_extensions
            ])
            for f in files_in_folder:
                resolved_path = f.resolve()
                if resolved_path not in seen_paths:
                    documents.append(f)
                    seen_paths.add(resolved_path)

    if not documents:
        print("Error: No supported documents found to process.")
        exit(1)

    # -------------------------------------------
    # Print header
    # -------------------------------------------

    print("")
    print("=" * 60)
    print("  Document to Markdown Converter")
    print("=" * 60)
    print(f"  Inputs   : {', '.join(args.inputs)}")
    print(f"  Output   : {output_folder}")
    print(f"  Pipeline : {args.pipeline}")
    print(f"  Documents: {len(documents)}")
    print("=" * 60)

    # -------------------------------------------
    # Temp directories
    # -------------------------------------------

    temp_assets_dir = Path("temp_assets")
    temp_chunks_dir = Path("temp_chunks")

    # -------------------------------------------
    # Process each document
    # -------------------------------------------

    batch_start = time.perf_counter()

    for index, document in enumerate(documents, start=1):

        print("")
        print("=" * 60)
        print(f"  Document {index}/{len(documents)}")
        print(f"  {document.name}")
        print("=" * 60)

        # Create benchmark
        benchmark = Benchmark()
        benchmark.document_name = document.name
        benchmark.document_type = document.suffix.lower()
        benchmark.file_size_mb = (
            document.stat().st_size / (1024 * 1024)
        )

        # Clear temp folders
        clear_folder("temp_assets")
        clear_folder("temp_chunks")

        for chunk_file in output_folder.glob("chunk_*.md"):
            chunk_file.unlink()

        # Convert .doc → .docx if needed
        converted_path = document

        if document.suffix.lower() == ".doc":
            converted_path = Path(
                convert_doc(document)
            )

        # Run pipeline
        try:

            if args.pipeline == "docling":

                result = process_docling_pipeline(
                    converted_path=converted_path,
                    output_dir=output_folder,
                    temp_assets_dir=temp_assets_dir,
                    temp_chunks_dir=temp_chunks_dir,
                    document_index=index,
                    ui=ui,
                )

            else:

                result = process_hybrid_pipeline(
                    converted_path=converted_path,
                    output_dir=output_folder,
                    temp_assets_dir=temp_assets_dir,
                    temp_chunks_dir=temp_chunks_dir,
                    document_index=index,
                    ui=ui,
                )

            final_markdown = result["markdown"]
            total_images = result["image_count"]
            timings = result["timings"]
            report = result["report"]
            analysis_times = result["analysis_times"]

            # -------------------------------------------
            # Print processing report
            # -------------------------------------------

            print_report(report)

            # -------------------------------------------
            # Populate benchmark
            # -------------------------------------------

            benchmark.total_time = timings["total"]
            benchmark.images_detected = total_images

            benchmark.stage_times = {
                "analysis": timings["analysis"],
                "chunking": timings["chunking"],
                "parsing": timings["parsing"],
                "image_analysis": timings["image_analysis"],
                "markdown_merge": timings["merge"],
            }

            benchmark.analysis_times = analysis_times

            benchmark.images_analyzed = report.images_analyzed
            benchmark.images_cached = report.images_cached
            benchmark.images_skipped = report.images_skipped
            benchmark.images_failed = report.images_failed

            benchmark.images_processed = (
                benchmark.images_detected
                - benchmark.images_skipped
            )

            # -------------------------------------------
            # Save benchmark HTML report
            # -------------------------------------------

            benchmark_html = generate_benchmark_report(benchmark)

            benchmark_filename = (
                f"{document.stem}_benchmark.html"
            )

            benchmark_path = output_folder / benchmark_filename

            benchmark_path.write_text(
                benchmark_html,
                encoding="utf-8"
            )

            print(f"\n  Benchmark : {benchmark_path}")
            print(f"  Markdown  : {final_markdown}")

        except Exception as e:

            print(f"\n  Pipeline failed: {e}")
            import traceback
            traceback.print_exc()

    # -------------------------------------------
    # Combine all documents
    # -------------------------------------------

    batch_time = time.perf_counter() - batch_start

    if len(documents) > 0:

        final_batch = combine_final_documents(output_folder)

        print("")
        print("=" * 60)
        print("  Batch Complete")
        print("=" * 60)
        print(f"  Documents Processed : {len(documents)}")
        print(f"  Total Time          : {batch_time:.2f} sec")
        print(f"  Combined Output     : {final_batch}")
        print("=" * 60)


if __name__ == "__main__":
    main()