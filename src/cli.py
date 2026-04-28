import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
from datetime import datetime
import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from .pipelines.ollama_pipe import run as run_ollama
from .pipelines.openai_pipe import run as run_openai
from .pipelines.azure_pipe import run as run_azure
from .pipelines.claude_pipe import run as run_claude
from .pipelines.google_pipe import run as run_google
from .pipelines.validation_pipe import run as run_validation
from .shared.saveToCSV import SaveToCSV
from .shared.config import get_settings


def file_folder(file_path: str) -> list[Path]:
    file_p = Path(file_path)

    # If path is to a file return that path, if path is to folder retrieve all file names to a list
    if file_p.is_file():
        if file_p.suffix.lower() not in {".pdf", ".jpg", ".png"}:
            raise ValueError(f"Provided file is not a PDF, JPG, or PNG: {file_path}")
        return [file_p]
    
    if file_p.is_dir():
        files = sorted(
            f for f in file_p.iterdir()
            if f.is_file() and f.suffix.lower() in {".pdf", ".jpg", ".png"}
        )

        if not files:
            raise ValueError(f"No valid files found in directory: {file_p}")

        return files
    
    raise ValueError(f"Provided path is not a file or directory: {file_path}")

def get_dataset_name(file_path: Path) -> str:

    if file_path.suffix:
        return file_path.parent.name
    
    return file_path.name

def normalize_dataset_name(dataset_name: str) -> str:
    dataset_name = dataset_name.lower()
    if "mio" in dataset_name:
        return "mio"
    elif "cord" in dataset_name:
        return "cord"
    elif "fatura" in dataset_name:
        return "fatura"
    else:
        raise ValueError(f"Unknown dataset: '{dataset_name}' — folder must contain 'mio', 'cord', or 'fatura'")

def _process(file_path: str, dataset_name: str, dataset_key:str, validation_folder_p: Path, args: argparse.Namespace, csv_writer: SaveToCSV | None, output_dir: Path) -> None:
    print(f"\nProcessing file: {file_path.name} with pipeline: {args.pipeline}")
    
    print(f"Dataset: {dataset_name}")

    if args.pipeline == "ollama":
        result = run_ollama(file_path, dataset_key, validation_folder_p, csv_writer, output_dir=output_dir, extractor=args.extractor)
    elif args.pipeline == "openai":
        result = run_openai(file_path, dataset_key, validation_folder_p, csv_writer, output_dir=output_dir)
    elif args.pipeline == "azure":
        result = run_azure(file_path, dataset_key, validation_folder_p, csv_writer, output_dir=output_dir)
    elif args.pipeline == "claude":
        result = run_claude(file_path, dataset_key, validation_folder_p, csv_writer, output_dir=output_dir)
    elif args.pipeline == "google":
        result = run_google(file_path, dataset_key, validation_folder_p, csv_writer, output_dir=output_dir)
    elif args.pipeline == "validation":
        result = run_validation(file_path)
    else:
        raise ValueError(f"Unknown pipeline: {args.pipeline}")

    if not args.quiet:
        print("----- FINAL JSON START -----")
        print(json.dumps(result.final, indent=2, ensure_ascii=False))
        print("----- FINAL JSON END -----")

    print("\nSaved files:")
    a = result.artifacts
    if a.raw_json_path:
        print("Raw JSON:", a.raw_json_path)
    if a.final_json_path:
        print("Final JSON:", a.final_json_path)
    if a.validation_score_path:
        print("Validation Score:", a.validation_score_path)
    if a.markdown_path:
        print("Markdown:", a.markdown_path)
    if a.validation_file_path:
        print("Validation File:", a.validation_file_path / f"{dataset_name}.json")

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Run a PDF, JPG, or PNG extraction pipeline on a file or all files of those types in a directory.",
        epilog=(
            "Use --pipeline validation to build the ground-truth file that "
            "other pipelines validate their output against."
        ),
    )
    ap.add_argument("path", help="Path to PDF, JPG, or PNG file or directory containing those files")
    ap.add_argument("--pipeline", 
                    choices=["ollama", "openai", "azure", "claude", "google", "validation"], 
                    required=True,
                    help=(
                        "ollama / openai / azure / claude / google: extract and validate against ground truth. "
                        "validation: extract via Azure and write as ground truth."
                    ),
    )
    ap.add_argument("--extractor",
                    choices=["glm_ocr", "docling"],
                    default=None,
                    help="Extractor to use (only applicable for ollama pipeline)"
    )
    ap.add_argument("--csv-mode",
                    choices=["run", "experiment"],
                    default="run",
                    help=(
                        "run: save a separate CSV for each run (default)."
                        "experiment: append all runs to a shared CSV per dataset."
                    ),
    )
    ap.add_argument("--runs", 
                    type=int, 
                    default=1, 
                    help="Number of times to run each dataset or file (default: 1)")
    
    ap.add_argument("--quiet", 
                    action="store_true", 
                    help="Don't print final JSON to console")
    
    args = ap.parse_args()
    
    if args.extractor and args.pipeline != "ollama":
        ap.error("--extractor is only supported for the ollama pipeline")

    if args.pipeline == "ollama" and args.extractor is None:
        args.extractor = "docling"  # apply default only for ollama

    # Retrieves the name of the files or file in a list
    files = file_folder(args.path)

    # get the path of the dataset and get only the name of the dataset folder and set to dataset name
    dataset_p = Path(args.path)
    dataset_name = get_dataset_name(dataset_p)          # "mio_test" or "mio_final" — used for paths/output
    dataset_key = normalize_dataset_name(dataset_name)  # "mio" — used for pipeline config

    # Set the path for the validation file folder based on the dataset folder name
    validation_folder_p = dataset_p.parent if dataset_p.suffix else dataset_p
    

    settings = get_settings()
    
    if args.extractor:
        pipeline_name = f"{args.pipeline}_{args.extractor}"
    else:
        pipeline_name = args.pipeline
    

    scoring_pipelines = {"ollama", "openai", "azure", "claude", "google"}
    for run_index in range(args.runs):
        if args.runs > 1:
            print(f"\n==============================")
            print(f"RUN {run_index + 1} of {args.runs}")
            print(f"==============================")
        
        run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Set ouput directory path and make sure the path exist
        output_dir = settings.output_dir / pipeline_name / dataset_name / run_timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        if args.pipeline in scoring_pipelines:
            if args.csv_mode == "experiment":
                # If in experiment mode, save all results to a shared CSV file for the dataset, rather than a separate CSV for each run
                csv_path = settings.output_dir / pipeline_name / dataset_name / f"results_{pipeline_name}.csv"
            else:
                # If in run mode, save to a separate CSV file for this run
                csv_path = output_dir / f"results_{pipeline_name}.csv"

            with SaveToCSV(csv_path, dataset_name, dataset_key, append=args.csv_mode == "experiment") as csv_writer:
                for file_name in files:
                    _process(file_name, dataset_name, dataset_key, validation_folder_p, args, csv_writer, output_dir)
        
        else:
            for file_name in files:
                _process(file_name, dataset_name, dataset_key, validation_folder_p, args, csv_writer=None, output_dir=output_dir)

        print(f"\nFiles processed this run: {len(files)}")

    print("\n==============================")
    print(f"Total runs: {args.runs}")
    print(f"Total files processed: {args.runs * len(files)}")
    print("==============================")

if __name__ == "__main__":
    main()