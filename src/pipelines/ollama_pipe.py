
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from ..shared.schema import schema, schemaFATURA, schemaCORD
from ..shared.prompts import ZEROSHOT, ZEROSHOTFATURA, ZEROSHOTCORD
from ..shared.normalize import canonicalize_json

from ..shared.validate import Validator
from ..shared.faturaVal import FaturaValidator
from ..shared.cordVal import validateCordExtract
#from ..shared.validator import get_validator

from ..shared.io import save_md, save_raw_json, save_final_json, save_validation_score
from ..shared.config import get_settings
from ..shared.types import PipelineArtifactPaths, PipelineResult
from ..shared.saveToCSV import SaveToCSV

from ..extractors.docling_extractor import extract_pages
from ..extractors.glm_ocr_extractor import call_glm_ocr
from ..providers.ollama_provider import call_ollama


PIPELINE_NAME = "ollama"

def base_prompt(dataset_name: str, ):
    if dataset_name == "mio":
        BASE_PROMPT = ZEROSHOT
    elif dataset_name == "fatura":
        BASE_PROMPT = ZEROSHOTFATURA
    elif dataset_name == "cord":
        BASE_PROMPT = ZEROSHOTCORD
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    return BASE_PROMPT

def build_prompt(text: str, dataset_name: str) -> str:
    parts = [
        base_prompt(dataset_name),
        "EXTRACT TEXT FROM THIS DOCUMENT:",
        f"<document>\n{text.strip()}\n</document>",
    ]
    return "\n\n".join(parts)


def run(file_path_str: str, dataset: str, validation_folder_path: Path, csv_writer: SaveToCSV, output_dir: Path, extractor: str) -> PipelineResult:
    settings = get_settings()
    file_path = Path(file_path_str)
    dataset_name = dataset

    run_id = datetime.now().strftime("%y%m%d-%H%M-%S")

    print(f"Extracting text from file: {file_path_str}...")

    if extractor == "docling":
        text = extract_pages(file_path_str)
    elif extractor == "glm_ocr":
        text = call_glm_ocr(file_path_str, settings)

    md_path = save_md(text, file_path, output_dir, run_id)

    prompt = build_prompt(text, dataset_name)

    print("Calling Ollama...")
    if dataset_name == "mio":
        raw_data = call_ollama(prompt, schema, settings)
    elif dataset_name == "fatura":
        raw_data = call_ollama(prompt, schemaFATURA, settings)
    elif dataset_name == "cord":
        raw_data = call_ollama(prompt, schemaCORD, settings)

    print("Saving and canonilize...")
    raw_path = save_raw_json(raw_data, file_path, output_dir, run_id)

    final_data = canonicalize_json(raw_data, source=PIPELINE_NAME)

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
            markdown_path=md_path,
            raw_json_path=raw_path,
            final_json_path=final_path,
            validation_score_path=score_path,
            validation_file_path=None,
        )
    )