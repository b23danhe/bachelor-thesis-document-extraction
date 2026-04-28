from __future__ import annotations

import json
from pathlib import Path
from typing import Any, NamedTuple

def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


class OutputPaths(NamedTuple):
    md: Path
    raw: Path
    final: Path
    score: Path

    @classmethod
    def build(cls, output_dir: Path, pdf_path: Path):
        stem = f"{pdf_path.stem}"
        return cls(
            md=output_dir / f"{stem}.md",
            raw=output_dir / f"{stem}-raw.json",
            final=output_dir / f"{stem}.json",
            score=output_dir / f"{stem}-validation_score.json"
        )

# -------------------------------------------------------------------------------------------------------------------------------------
# Save functions
# -------------------------------------------------------------------------------------------------------------------------------------

def save_md(
        md: str, 
        pdf_path: Path,
        output_dir: Path,
        run_id: str,
) -> Path:
    
    out_dir = ensure_output_dir(output_dir / "markdown")
    md_path = OutputPaths.build(out_dir, pdf_path).md
    md_path.write_text(md, encoding="utf-8")
    return md_path.relative_to(output_dir)


def save_raw_json(
        raw: str | Any, 
        pdf_path: Path,
        output_dir: Path,
        run_id: str,
) -> Path:
    
    raw_path = OutputPaths.build(output_dir, pdf_path).raw

    if isinstance(raw, str):
        data = json.loads(raw)
    else:
        data = raw
    _write_json(raw_path, data)

    return raw_path.relative_to(output_dir)


def save_final_json(
        final: Any, 
        pdf_path: Path,
        output_dir: Path,
        run_id: str,
) -> Path:
    
    final_path = OutputPaths.build(output_dir, pdf_path).final
    _write_json(final_path, final)

    return final_path.relative_to(output_dir)


def save_validation_score(
        score: Any, 
        pdf_path: Path,
        output_dir: Path,
        run_id: str,
) -> Path:
    
    score_path = OutputPaths.build(output_dir, pdf_path).score
    _write_json(score_path, score)

    return score_path.relative_to(output_dir)


def save_to_validation_file(
        data: Any,
        pdf_path: Path,
        validation_dir: Path,
) -> Path:
    out_dir = ensure_output_dir(validation_dir / "validation")
    validation_path = out_dir / "validation_file.json"

    existing: dict[str, Any] = {}
    if validation_path.exists():
        try:
            existing = json.loads(validation_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    
    existing[pdf_path.stem] = data
    _write_json(validation_path, existing)

    return validation_path

#-------------------------------------------------------------------------------------------------------------------------------------
# Helper function to write JSON data to a file
#-------------------------------------------------------------------------------------------------------------------------------------

def _write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)