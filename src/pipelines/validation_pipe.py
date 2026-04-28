from __future__ import annotations

from pathlib import Path
from datetime import datetime

from ..shared.normalize import canonicalize_json
from ..shared.io import save_to_validation_file
from ..shared.config import get_settings
from ..shared.types import PipelineArtifactPaths, PipelineResult
from ..providers.azure_provider import call_azure

PIPELINE_NAME = "validation"

def _field_content(doc, name: str) -> str | None:

    if not doc or not getattr(doc, "fields", None):
        return None
    field = doc.fields.get(name)
    return getattr(field, "content", None) if field else None

def _extract_article_numbers(doc) -> list[str]:
    if not doc or not getattr(doc, "fields", None):
        return []
    
    field = doc.fields.get("ArticleNumber")
    if not field:
        return []
    
    arr = getattr(field, "value_array", None) or []

    out: list[str] = []
    for item in arr:
        val_obj = getattr(item, "value_object", None)
        if not isinstance(val_obj, dict):
            continue

        article_number = val_obj.get("article_number")
        if not article_number:
            continue

        val_str = getattr(article_number, "value_string", None) or getattr(article_number, "content", None)
        if val_str:
            out.append(val_str)

    return out

def run(pdf_path: Path) -> PipelineResult:
    settings = get_settings()

    print(f"[{PIPELINE_NAME}] Extracting ground truth from PDF: {pdf_path}...")
    result = call_azure(str(pdf_path), settings)

    doc = result.documents[0] if getattr(result, "documents", None) else None

    order_number = _field_content(doc, "OrderNumber")
    delivery_date = _field_content(doc, "Delivery date")
    delivery_week = _field_content(doc, "Delivery week")
    article_numbers = _extract_article_numbers(doc)

    data = {
        "OrderNumber": {
            "value": order_number
        },
        "DeliveryDate": {
            "value": delivery_date
        },
        "DeliveryWeek": {
            "value": delivery_week
        },
        "ArticleNumbers": article_numbers
    }

    data = canonicalize_json(data, source=PIPELINE_NAME)

    validation_file_path = save_to_validation_file(data, pdf_path, settings.validate_input_dir)
    print(f"[{PIPELINE_NAME}] Saved validation file for {pdf_path.stem} at: {validation_file_path}")

    return PipelineResult(
        final=data,
        raw=None,
        artifacts=PipelineArtifactPaths(
            markdown_path=None,
            raw_json_path=None,
            final_json_path=None,
            validation_score_path=None,
            validation_file_path=validation_file_path,
        ),
    )