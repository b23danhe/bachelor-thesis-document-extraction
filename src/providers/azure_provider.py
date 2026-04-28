from __future__ import annotations

from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

from ..shared.config import Settings

def call_azure(pdf_path: str | Path, settings: Settings, azure_model_id: str):                                                                                                                                                                                                                                                                                                                                                                                                                                     
    endpoint = settings.azure_endpoint.rstrip("/")
    key = settings.azure_key
    model_id = azure_model_id

    print(f"Calling Azure Document Intelligence with model ID: {model_id}")

    pdf_path = Path(pdf_path)

    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    with open(pdf_path, "rb") as f:
        poller = client.begin_analyze_document(
            model_id=model_id,
            body=f
        )

    return poller.result()