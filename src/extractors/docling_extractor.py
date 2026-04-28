
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption, ImageFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions

def _build_converter() -> DocumentConverter:
	pipeline_options = PdfPipelineOptions()
	pipeline_options.do_ocr = True
	
	# Hybrid OCR: use embedded text when present, OCR when needed
	pipeline_options.ocr_options = TesseractCliOcrOptions(force_full_page_ocr=False)

	image_pipeline_options = PdfPipelineOptions()
	image_pipeline_options.do_ocr = True
	image_pipeline_options.ocr_options = TesseractCliOcrOptions(force_full_page_ocr=True)

	return DocumentConverter(
			format_options={
							InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
							InputFormat.IMAGE: ImageFormatOption(),
        	}
    )
    
# Build once at module load time, reuse across calls
_CONVERTER = _build_converter()

def extract_pages(file_path: str) -> str:
	file_path = Path(file_path)
	result = _CONVERTER.convert(Path(file_path))
	md = result.document.export_to_text()
	return md.strip()