import os
from typing import Optional
from google.api_core.client_options import ClientOptions
from google.cloud import documentai

def call_google(project_id: str, location: str, processor_id: str, file_path: str, mime_type: str,  processor_version_id: Optional[str] = None,) -> dict:
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    if processor_version_id:
        name = client.processor_version_path(
            project_id, location, processor_id, processor_version_id
        )
    else:
        name = client.processor_path(project_id, location, processor_id)

    with open(file_path, "rb") as f:
        image_content = f.read()

    request = documentai.ProcessRequest(
        name=name,
        raw_document=documentai.RawDocument(
            content=image_content,
            mime_type=mime_type
        ),
    )

    return client.process_document(request=request).document        
    



