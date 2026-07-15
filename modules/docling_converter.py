from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)

# ----------------------------------------
# Configure PDF pipeline ONCE
# ----------------------------------------

pdf_pipeline_options = PdfPipelineOptions()

pdf_pipeline_options.images_scale = 1
pdf_pipeline_options.generate_picture_images = True
pdf_pipeline_options.generate_page_images = False

# ----------------------------------------
# Create converters ONCE
# ----------------------------------------

PDF_CONVERTER = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pdf_pipeline_options
        )
    }
)

DOCX_CONVERTER = DocumentConverter()