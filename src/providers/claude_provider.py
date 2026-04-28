from __future__ import annotations

from pathlib import Path
from anthropic import Anthropic
import json

def call_claude(pdf_path: str, prompt: str, schema: dict, *, api_key: str, model: str):

    client = Anthropic(api_key=api_key)

    pdf_p = Path(pdf_path)

    if pdf_p.suffix.lower() == ".pdf":
        input_type = "document"

    elif pdf_p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
        input_type = "image"
    
    with pdf_p.open("rb") as f:
        file = client.beta.files.upload(
            file=(pdf_p.name + pdf_p.suffix.lower(), f)
        )

    response = client.beta.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        betas=["files-api-2025-04-14"],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": input_type,
                        "source": {"type": "file", "file_id": file.id},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": schema
            }
        }
    )
    return json.loads(response.content[0].text)