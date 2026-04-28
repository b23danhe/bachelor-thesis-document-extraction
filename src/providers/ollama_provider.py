
import requests

def call_ollama(prompt: str, schema: dict, settings):

    ollama_url = settings.ollama_url.rstrip("/")
    model = settings.ollama_model
    print(prompt)
    if not ollama_url:
        raise SystemExit("OLLAMA_URL is not set. Example: http://host.docker.internal:11434")

    r = requests.post(
        f"{ollama_url}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": schema,
            "options": {
                "temperature": 0,
                "num_ctx": 16384
            },
        },
        timeout=900,
    )
    r.raise_for_status()
    return r.json()["response"]