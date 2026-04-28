from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from ..shared.schema import schema
from ..shared.prompts import ZEROSHOT as BASE_PROMPT
from ..shared.normalize import canonicalize_json
from ..shared.validate import Validator
from ..shared.io import save_md, save_raw_json, save_final_json, save_validation_score
from ..shared.config import get_settings
from ..shared.types import PipelineArtifactPaths, PipelineResult
from ..shared.saveToCsv import SaveToCSVMio

from ..extractors.docling_extractor import extract_pages
from ..providers.ollama_provider import call_ollama

PIPELINE_NAME = "ollama"


def build_prompt(text: str) -> str:
    parts = [
        BASE_PROMPT,
        "TEXT TO EXTRACT FROM:",
        text.strip()
    ]
    return "\n\n".join(parts)


def run(pdf_path: str, csv_writer: SaveToCSVMio, output_dir: Path) -> PipelineResult:
    settings = get_settings()
    pdf_p = Path(pdf_path)

    run_id = datetime.now().strftime("%y%m%d-%H%M-%S")

    print(f"Extracting text from PDF: {pdf_p}...")
    text = extract_pages(str(pdf_p))
    md_path = save_md(text, pdf_p, output_dir, run_id)

    prompt = build_prompt(text)

    print("Calling Ollama...")
    raw = call_ollama(prompt, schema, settings)

    raw_path = save_raw_json(raw, pdf_p, output_dir, run_id)

    data = canonicalize_json(raw, source=PIPELINE_NAME)

    final_path = save_final_json(data, pdf_p, output_dir, run_id)

    validate_json = Validator(settings.validate_input_dir)
    validation_score = validate_json.validateJson(data, pdf_p)
    csv_writer.add_line({**validation_score, "FileName": pdf_p.name})

    score_path = save_validation_score(validation_score, pdf_p, output_dir, run_id)

    return PipelineResult(
        final=data,
        raw=raw,
        artifacts=PipelineArtifactPaths(
            markdown_path=md_path,
            raw_json_path=raw_path,
            final_json_path=final_path,
            validation_score_path=score_path,
            validation_file_path=None,
        )
    )