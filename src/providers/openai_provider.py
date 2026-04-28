from pathlib import Path
from openai import OpenAI

def call_openai(pdf_path: str, prompt: str, schema: dict, *, api_key: str, model: str):

    client = OpenAI(api_key=api_key)

    pdf_p = Path(pdf_path)

    if pdf_p.suffix.lower() == ".pdf":
        input_type = "input_file"

    elif pdf_p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
        input_type = "input_image"
    
    with pdf_p.open("rb") as f:
        file = client.files.create(
            file=(pdf_p.name + pdf_p.suffix.lower(), f),
            purpose="user_data"
        )

    response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": input_type, "file_id": file.id},
                        {"type": "input_text", "text": prompt},
                    ],
                }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "response",
                    "schema": schema,
                    "strict": False
                }
            }
    )

    return response.output_text