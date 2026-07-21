import fitz
import pymupdf4llm

pdf_path = "279pages.pdf"   # Replace with your PDF path

doc = fitz.open(pdf_path)

markdown = pymupdf4llm.to_markdown(doc)

with open("output_pymupdf4llm.md", "w", encoding="utf-8") as f:
    f.write(markdown)

print("Markdown generated successfully!")