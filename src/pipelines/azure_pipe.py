from __future__ import annotations

from pathlib import Path
from datetime import datetime

from ..shared.normalize import canonicalize_json

from ..shared.validate import Validator
from ..shared.faturaVal import FaturaValidator
from ..shared.cordVal import validateCordExtract
#from ..shared.validator import get_validator

from ..shared.io import save_raw_json, save_final_json, save_validation_score
from ..shared.saveToCSV import SaveToCSV
from ..shared.config import get_settings
from ..shared.types import PipelineArtifactPaths, PipelineResult
from ..providers.azure_provider import call_azure

PIPELINE_NAME = "azure"

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
    
    arr = getattr(field, "value_array", None)
    if not arr:  
        return []
    out: list[str] = []
    for item in arr:
        val_obj = getattr(item, "value_object", None)
        if not isinstance(val_obj, object):
            continue

        article_number = val_obj.get("article_number")
        if not article_number:
            continue

        val_str = getattr(article_number, "value_string", None) or getattr(article_number, "content", None)
        if val_str:
            out.append(val_str)

    return out

def _extract_items(doc, fields: list[str]) -> list:
    if not doc or not getattr(doc, "fields", None):
        return []

    field = doc.fields.get("Item")
    if not field or not field.value_array:
        return []

    out = []
    for item in field.value_array:
        val_obj = getattr(item, "value_object", None)
        if not val_obj:
            continue
        row = {}
        for f in fields:
            cell = val_obj.get(f)
            row[f] = (getattr(cell, "value_string", None) or getattr(cell, "content", None)) if cell else None
            row[f"{f}_confidence"] = getattr(cell, "confidence", None) if cell else None
        out.append(row)

    return out

def _field_confidence(doc, name: str) -> float | None:
    if not doc or not getattr(doc, "fields", None):
        return None
    field = doc.fields.get(name)
    return getattr(field, "confidence", None) if field else None


def _mio(doc) -> dict:
    return {
        "OrderNumber": {"value": _field_content(doc, "OrderNumber"), "confidence": _field_confidence(doc, "OrderNumber")},
        "DeliveryDate": {"value": _field_content(doc, "Delivery date"), "confidence": _field_confidence(doc, "Delivery date")},
        "DeliveryWeek": {"value": _field_content(doc, "Delivery week"), "confidence": _field_confidence(doc, "Delivery week")},
        "ArticleNumbers": _extract_article_numbers(doc),
    }

def _cord(doc) -> dict:
    return {
        "TotalSum": {"value": _field_content(doc, "Total"), "confidence": _field_confidence(doc, "Total")},
        "LineItems": _extract_items(doc, fields=["Name", "Price"]),
    }


def _fatura(doc) -> dict:
    return {
        "DueDate": {"value": _field_content(doc, "DueDate"), "confidence": _field_confidence(doc, "DueDate")},
        "TotalSum": {"value": _field_content(doc, "Total"), "confidence": _field_confidence(doc, "Total")},
        "LineItems": _extract_items(doc, fields=["Name", "Quantity", "Price"]),
    }

def run(file_path_str: str, dataset: str, validation_folder_path: Path, csv_writer: SaveToCSV, output_dir: Path) -> None:
    settings = get_settings()
    file_path = Path(file_path_str)
    dataset_name = dataset

    run_id = datetime.now().strftime("%y%m%d-%H%M-%S")

    print(f"Extracting text from PDF: {file_path.name}...")

    if dataset_name == "mio":
        azure_model_id = settings.azure_model_id_mio
    elif dataset_name == "fatura":
        azure_model_id = settings.azure_model_id_fatura
    elif dataset_name == "cord":
        azure_model_id = settings.azure_model_id_cord
    
    result = call_azure(file_path_str, settings, azure_model_id)

    if hasattr(result, "model_dump"):
        raw_data = result.model_dump()
    elif hasattr(result, "as_dict"):
        raw_data = result.as_dict()
    else:
        raw_data = {"type": str(type(result)), "note": "Result object does not have model_dump or as_dict method"}
    
    raw_path = save_raw_json(raw_data, file_path, output_dir, run_id)

    doc = result.documents[0] if getattr(result, "documents", None) else None

    if dataset_name == "mio":
        final_data = _mio(doc)
    elif dataset_name == "cord":
        final_data = _cord(doc)
    elif dataset_name == "fatura":
        final_data = _fatura(doc)

    final_data = canonicalize_json(final_data, source=PIPELINE_NAME)

    final_path = save_final_json(final_data, file_path, output_dir, run_id)

    if dataset_name == "mio": 
        validate_json = Validator(validation_folder_path, dataset_name)
        validation_score = validate_json.validateJson(final_data, file_path)
        csv_writer.add_line({**validation_score, "FileName": file_path.name})
    elif dataset_name == "fatura":
        validate_json = FaturaValidator(final_data, dataset_name, validation_folder_path, file_path)
        validation_score = validate_json.get_score()
        csv_writer.add_line({**validation_score, "FileName": file_path.name})
    elif dataset_name == "cord":
        validation_score = validateCordExtract(final_data, validation_folder_path, Path(file_path))
        csv_writer.add_line({**validation_score, "FileName": file_path.name})

    score_path = save_validation_score(validation_score, file_path, output_dir, run_id)

    return PipelineResult(
        final=final_data,
        raw=raw_data,
        artifacts=PipelineArtifactPaths(
            markdown_path=None,
            raw_json_path=raw_path,
            final_json_path=final_path,
            validation_score_path=score_path,
            validation_file_path=None,
        )
    )

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(r"C:\Users\Carl\Desktop\exjobb\Ex-jobb-2026\.env")
    
    from ..providers.azure_provider import call_azure  # already imported above
    from ..shared.config import get_settings

    settings = get_settings()
    
    file_path = r"C:\Users\Carl\Desktop\exjobb\Ex-jobb-2026\PDFs\cord_test_1.jpg"
    
    result = call_azure(file_path, settings)
    doc = result.documents[0] if getattr(result, "documents", None) else None
    
    # Test whichever dataset you want
    final_data = _cord(doc)
    
    import json
    print(json.dumps(final_data, indent=2))