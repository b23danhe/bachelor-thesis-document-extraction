
import requests
from ..converters.pymupdf_converter import pdf_to_images

def call_glm_ocr(pdf_path: str, settings):
    pages = pdf_to_images(pdf_path)
    ollama_url = settings.ollama_url.rstrip("/")
    model = settings.ollama_ocr_model

    if not ollama_url:
        raise SystemExit("OLLAMA_URL is not set.")
    
    all_text = []

    for page in pages:
        r = requests.post(
            f"{ollama_url}/api/chat",
            json={
                "model": model,
                "stream": False,
                "messages": [
                    {
                        "role": "user",
                        "content": "Text Recognition:",
                        "images": [page["base64"]],
                    }
                ],
                "options": {"temperature": 0},
            },
            timeout=900,
        )
        r.raise_for_status()
        all_text.append(r.json()["message"]["content"])
    result = "\n\n".join(all_text)
    print(result)
    return result


