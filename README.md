# Document extraction pipeline
Following is the installation instructions for the extraction pipeline that was used during the information teknology thesis project in spring 2026.

## Requirements
- Python 3.11+ (recommended: 3.12 or 3.13)
- macOS / Linux / Windows
- OpenAI API key (for cloud pipeline)
- Anthropic API key (for Sonnet 4.6)
- Ollama (for local LLM pipeline)
- Azure documentIntelligence (for Azure pipeline)
- Google Documents (for Google pipeline)
- Optional:
    - Only set up the pipeline you whant to run

## Installation
1. ### Clone the repository
2. ### Create virtual environment
Create venv:
<br>( for windows you might need to switch "python3" to "py" or "python" )
``` bash
python3 -m venv .venv
source .venv/bin/activate
```

You should now see:
```
(.venv)
```
3. ### Install dependencies
``` bash
pip install --upgrade pip
pip install -r requirements.txt
```
4. ### Create .env file
Create a file named `.env`in project root with the following environmet variables:

    OLLAMA_URL=http://127.0.0.1:11434
    OLLAMA_MODEL=qwen3:8b
    OLLAMA_OCR_MODEL=glm-ocr:latest

    AZURE_ENDPOINT=link_to_azure_endpoint
    AZURE_KEY= your_api_key
    AZURE_MODEL_ID_CORD=model_id
    AZURE_MODEL_ID_FATURA=model_id
    AZURE_MODEL_ID_MIO=model_id

    OPENAI_API_KEY= your_api_key
    OPENAI_MODEL=gpt-5.2

    CLAUDE_API_KEY= your_api_key
    CLAUDE_MODEL=sonnet-4.6

    OUTPUT_DIR=./output
    HF_HOME=./hf_cache
5. ### Create Input-folders
Create three folders in the root-folder and name them: 
    
    mio
    fatura
    cord

This is where you place the folder with the dataset or files to be extracted.

Also place the JSON-file containing the "ground truth" for each dataset in the respective folder. Name the file with the same name as the folder it's in (e.g mio/mio.json).

This does not apply for the cord dataset as each file in the dataset has it's own "ground truth" file.

---
# How to use the pipelines

## Run single PDF
### Ollama
Run with your desired pipeline

Options for pipelinename:
- ollama
- openai
- claude
- azure
- google
 
*(Filename should be a .pdf, .jpg or .png)* 
<br>Example: test.png

``` bash
python -m src.cli foldername/filename --pipeline pipelinename
```
You can also choose between two different extraction tools (**Only Ollama**)
<br>
Options for toolname:
- docling
- glm_ocr

``` bash
python -m src.sli foldername/filename --pipeline ollama --extractor toolname
```

## Run entire folder

``` bash
python -m src.cli foldername --pipeline pipelinename
```
---    
# Output
Results are stored in:

    output/<pipelinename>/<run_id>

Each run generates:
-   `*-raw.json` → raw model output
-   `*.json` → normalized & validated JSON
-   `*.csv` → Results from the run
-   `markdown/` (Docling output when applicable)
---
# Optional: Ollama setup
Install Ollama from:
https://ollama.com

Pull model:
``` bash
ollama pull qwen3:8b
```
To be able to run GLM-OCR extraction:
```bash
ollama pull glm-ocr:latest
```
Start server:
``` bash
ollama serve
```
