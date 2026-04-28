from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

@dataclass
class PipelineArtifactPaths:
    raw_json_path: Path | None
    final_json_path: Path | None
    validation_score_path: Path | None
    markdown_path: Path | None = None
    validation_file_path: Path | None = None
    

@dataclass
class PipelineResult:
    final: Any
    raw: Any | None
    artifacts: PipelineArtifactPaths