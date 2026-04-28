
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass(frozen=True)
class Settings:
    project_root: Path

    # Ollama settings
    ollama_url: str
    ollama_model: str
    ollama_ocr_model: str

    #Azure settings
    azure_endpoint: str
    azure_key: str
    azure_model_id_mio: str
    azure_model_id_fatura: str
    azure_model_id_cord: str

    #Goolge settings
    google_api: str

    # OpenAI settings
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-5.2"

    # Claude settings
    claude_api_key: Optional[str] = None
    claude_model: Optional[str] = None

    # Output/cache settings
    output_dir: Path = Path("output")
    hf_home: Path = Path("hf_cache")

def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[2]

    ollama_url = os.getenv("OLLAMA_URL")
    ollama_model = os.getenv("OLLAMA_MODEL")
    ollama_ocr_model = os.getenv("OLLAMA_OCR_MODEL")

    azure_endpoint = os.getenv("AZURE_ENDPOINT")
    azure_key = os.getenv("AZURE_KEY")
    azure_model_id_mio = os.getenv("AZURE_MODEL_ID_MIO")
    azure_model_id_fatura = os.getenv("AZURE_MODEL_ID_FATURA")
    azure_model_id_cord = os.getenv("AZURE_MODEL_ID_CORD")

    google_api = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not google_api:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is not set in .env")

    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL")

    claude_api_key = os.getenv("CLAUDE_API_KEY")
    claude_model = os.getenv("CLAUDE_MODEL")

    output_dir = Path(os.getenv("OUTPUT_DIR", str(project_root / "output")))
    output_dir.mkdir(parents=True, exist_ok=True)

    hf_home = Path(os.environ.setdefault("HF_HOME", str(project_root / "hf_cache")))
    hf_home.mkdir(parents=True, exist_ok=True)

    return Settings(
        project_root=project_root,

        ollama_url=ollama_url,
        ollama_model=ollama_model,
        ollama_ocr_model=ollama_ocr_model,

        azure_endpoint=azure_endpoint,
        azure_key=azure_key,
        azure_model_id_mio=azure_model_id_mio,
        azure_model_id_fatura=azure_model_id_fatura,
        azure_model_id_cord=azure_model_id_cord,

        google_api=google_api,

        openai_api_key=openai_api_key,
        openai_model=openai_model,

        claude_api_key=claude_api_key,
        claude_model=claude_model,

        output_dir=output_dir,
        hf_home=hf_home
    )
