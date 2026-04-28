import os
from pathlib import Path
from datetime import datetime

from ..shared.normalize import canonicalize_json

from ..shared.validate import Validator
from ..shared.faturaVal import FaturaValidator
from ..shared.cordVal import validateCordExtract

from ..shared.io import save_raw_json, save_final_json, save_validation_score
from ..shared.saveToCSV import SaveToCSV
from ..shared.types import PipelineArtifactPaths, PipelineResult

from ..providers.google_provider import call_google

PIPELINE_NAME = "google"


def run(file_path_str: str, dataset: str, validation_folder_path: Path, csv_writer: SaveToCSV, output_dir: Path) -> PipelineResult:

    file_path = Path(file_path_str)
    run_id = datetime.now().strftime("%y%m%d-%H%M-%S")

    print(f"Extracting text from file: {file_path.name}...")

    project_id = "orderconfprocessor"
    location = "eu"
    mime_type = "application/pdf" if dataset == "mio" else "image/jpeg"

    if dataset == "mio":
        processor_id = "f0cbb3f9e8c90d98"
        processor_version_id = "a9e5b665fd4f0727"
    elif dataset == "cord":
        processor_id = "2367849348ea48be"
        processor_version_id = "b08092896fa4316b"
    elif dataset == "fatura":
        processor_id = "de3c76c02f24aa54"
        processor_version_id = "e8c68e5034192110"
    
    result = call_google(
        project_id=project_id,
        location=location,
        processor_id=processor_id,
        processor_version_id=processor_version_id,
        file_path=file_path_str,
        mime_type=mime_type,
    )

    document = result

    raw_data = {"type": str(type(result)), "note": "Goole DocumentAI result object"}
    raw_path = save_raw_json(raw_data, file_path, output_dir, run_id)

    if dataset == "mio":
        extracted = {
            "FileName": {"value": os.path.basename(file_path)},
            "OrderNumber": {"value": None},
            "DeliveryDate": {"value": None},
            "DeliveryWeek": {"value": None},
            "ArticleNumbers": [],
            "RegistrationDate": None,
            "SupplierOrderNumber": None,
        }
        for entity in document.entities:
            if entity.properties:
                for prop in entity.properties:
                    if prop.type_ == "ArticleID":
                        extracted["ArticleNumbers"].append(prop.mention_text)
            else:
                if entity.type_ == "ReciverOrderNumber":
                    extracted["OrderNumber"]["value"] = int(entity.mention_text) if entity.mention_text.isdigit() else entity.mention_text
                    extracted["OrderNumber"]["confidence"] = round(entity.confidence, 4)
                elif entity.type_ == "DeliveryDate":
                    extracted["DeliveryDate"]["value"] = entity.mention_text
                    extracted["DeliveryDate"]["confidence"] = round(entity.confidence, 4)
                elif entity.type_ == "DeliveryWeek":
                    extracted["DeliveryWeek"]["value"] = entity.mention_text
                    extracted["DeliveryWeek"]["confidence"] = round(entity.confidence, 4)
                elif entity.type_ == "RegistrationDate":
                    extracted["RegistrationDate"] = entity.mention_text
                elif entity.type_ == "SupplierOrderNumber":
                    extracted["SupplierOrderNumber"] = entity.mention_text
        

    elif dataset == "cord":
        extracted = {
            "TotalSum": {"value": None},
            "LineItems": [],
        }
        for entity in document.entities:
            if entity.type_ == "Item":
                item = {"Name": None, "Price": None}
                for prop in entity.properties:
                    if prop.type_ == "Name":
                        item["Name"] = prop.mention_text
                        item["Name_confidence"] = round(prop.confidence, 4)
                    elif prop.type_ == "Price":
                        item["Price"] = prop.mention_text
                        item["Price_confidence"] = round(prop.confidence, 4)
                extracted["LineItems"].append(item)
            elif entity.type_ == "Total":
                extracted["TotalSum"]["value"] = entity.mention_text
                extracted["TotalSum"]["confidence"] = round(entity.confidence, 4) 

        
    elif dataset == "fatura":
        extracted = {
            "DueDate": {"value": None},
            "TotalSum": {"value": None},
            "LineItems": [],
        }
        for entity in document.entities:
            if entity.type_ == "Item":
                item = {"Name": None, "Quantity": None, "Price": None}
                for prop in entity.properties:
                    if prop.type_ == "Name":
                        item["Name"] = prop.mention_text
                        item["Name_confidence"]     = round(prop.confidence, 4) 
                    elif prop.type_ == "Price":
                        item["Price"] = prop.mention_text
                        item["Price_confidence"]    = round(prop.confidence, 4)
                    elif prop.type_ == "Quantity":
                        item["Quantity"] = prop.mention_text
                        item["Quantity_confidence"] = round(prop.confidence, 4)
                extracted["LineItems"].append(item)
            elif entity.type_ == "Total":
                extracted["TotalSum"]["value"] = entity.mention_text
                extracted["TotalSum"]["confidence"] = round(entity.confidence, 4)
            elif entity.type_ == "DueDate":
                extracted["DueDate"]["value"] = entity.mention_text
                extracted["DueDate"]["confidence"] = round(entity.confidence, 4) 

    else:
        raise ValueError(f"Unknown dataset: {dataset}")
    
    final_data = canonicalize_json(extracted, source=PIPELINE_NAME)
    final_path = save_final_json(final_data, file_path, output_dir, run_id)

    if dataset == "mio":
        validate_json = Validator(validation_folder_path, dataset)
        validation_score = validate_json.validateJson(final_data, file_path)
        csv_writer.add_line({**validation_score, "FileName": file_path.name})
    elif dataset == "fatura":
        validate_json = FaturaValidator(final_data, dataset, validation_folder_path, file_path)
        validation_score = validate_json.get_score()
        csv_writer.add_line({**validation_score, "FileName": file_path.name})
    elif dataset == "cord":
        validation_score = validateCordExtract(final_data, validation_folder_path, file_path)
        csv_writer.add_line({**validation_score, "FileName": file_path.name})
    
    score_path = save_validation_score(validation_score, file_path, output_dir, run_id)

    return PipelineResult(
        final=final_data,
        raw=raw_data,
        artifacts=PipelineArtifactPaths(
            markdown_path=None,
            raw_json_path=raw_path,
            final_json_path=final_path,
            validation_score_path=score_path,
            validation_file_path=None,
        )
    )


  
if __name__ == "__main__":

    from dotenv import load_dotenv
    #Something odd when i tried to import the files, somethingt to look into
    load_dotenv(r"C:\Users\Carl\Desktop\exjobb\Ex-jobb-2026\.env") 
    result = run(
        file_path=r"C:\Users\Carl\Desktop\exjobb\Ex-jobb-2026\cord_v2\test\cord_test_24.jpg",
        dataset="cord",
        #validation_folder_path=Path("some/path"),
        #csv_writer=None,
        #output_dir=Path("some/output"),
    )
    from pathlib import Path
    Finalresult = validateCordExtract(result, Path(r"C:\Users\Carl\Desktop\exjobb\Ex-jobb-2026\cord_v2\test"), 
                            Path(r"C:\Users\Carl\Desktop\exjobb\Ex-jobb-2026\cord_v2\test\cord_test_24.jpg"))
    print("CORD RESULT:  ", Finalresult)
