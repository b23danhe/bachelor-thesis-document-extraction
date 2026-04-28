from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..shared.schema import schema, schemaFATURA, schemaCORD
from ..shared.prompts import ZEROSHOT, ZEROSHOTFATURA, ZEROSHOTCORD
from ..shared.normalize import canonicalize_json

from ..shared.validate import Validator
from ..shared.faturaVal import FaturaValidator
from ..shared.cordVal import validateCordExtract
#from ..shared.validator import get_validator

from ..shared.io import save_raw_json, save_final_json, save_validation_score
from ..shared.config import get_settings
from ..shared.types import PipelineArtifactPaths, PipelineResult
from ..shared.saveToCSV import SaveToCSV

from ..providers.claude_provider import call_claude

PIPELINE_NAME = "claude"

def run(file_path_str: str, dataset: str, validation_folder_path: Path, csv_writer: SaveToCSV, output_dir: Path) -> None:
    settings = get_settings()
    file_path = Path(file_path_str)
    dataset_name = dataset

    run_id = datetime.now().strftime("%y%m%d-%H%M-%S")

    if not settings.claude_api_key:
        raise SystemExit("CLAUDE_API_KEY is not set.")

    print(f"Extracting text from file: {file_path.name}...")
    print("Calling Claude...")
    if dataset_name == "mio":
        raw_data = call_claude(file_path_str, ZEROSHOT, schema, api_key=settings.claude_api_key, model=settings.claude_model)
    elif dataset_name == "fatura":
        raw_data = call_claude(file_path_str, ZEROSHOTFATURA, schemaFATURA, api_key=settings.claude_api_key, model=settings.claude_model)
    elif dataset_name == "cord":
        raw_data = call_claude(file_path_str, ZEROSHOTCORD, schemaCORD, api_key=settings.claude_api_key, model=settings.claude_model)

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
        validation_score = validateCordExtract(final_data, validation_folder_path, file_path)
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