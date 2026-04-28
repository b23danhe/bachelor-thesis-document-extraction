import json
from pathlib import Path


class Validator:
    # Abstract base validator.

    def __init__(self, validation_file_dir: str | Path, dataset_name: str):
        self.validation_file_path = Path(validation_file_dir / f"{dataset_name}.json")
        with open(self.validation_file_path, "r") as file:
            self.goldenSTD: dict = json.load(file)

    def loadScore(self) -> dict:
        raise NotImplementedError

    def validateJson(self, inputData: dict, file_path: Path) -> dict:
        raise NotImplementedError
    
def get_validator(dataset: str, validation_file_dir: str | Path) -> Validator:

    # Return the correct Validator subclass for the specific dataset name

    from .validators import MioValidator, CordValidator, FaturaValidator

    validators ={
        "mio":      MioValidator,
        "cord":     CordValidator,
        "fatura":   FaturaValidator,
    }

    dataset_key = dataset.lower().strip()
    if dataset_key not in validators:
        raise ValueError(
            f"Unknown dataset"
        )
    
    return validators[dataset_key](validation_file_dir)
