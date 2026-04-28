
from __future__ import annotations
import csv
from pathlib import Path


class SaveToCSV:
    def __init__(self, output_path: str | Path, dataset_name: str, dataset_key: str, append: bool = False):
        self.outPutPath = output_path
        self.dataset_name = dataset_name
        self.dataset_key = dataset_key
        self.append = append
        self.fieldnames = self._get_fieldnames()
        self.csvfile = None
        self.writer = None

    def __enter__(self) -> SaveToCSV:
        file_exists = self.outPutPath.exists() and self.outPutPath.stat().st_size > 0
        mode = 'a' if self.append else 'w'
        self.csvfile = open(self.outPutPath, mode , newline='')
        self.writer = csv.DictWriter(self.csvfile, fieldnames=self.fieldnames, extrasaction="ignore")
        # Only write header if not appending to an existing file
        if not self.append or not file_exists:
            self.writer.writeheader()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.csvfile:
            self.csvfile.close()

    def _get_fieldnames(self) -> list[str]:
        MAX_ITEMS = 20
        if self.dataset_key == "mio":
            return [
                "FileName",
                "ON Score", "ON Extracted", "ON Expected", "ON Error", "ON error_description",
                "DD Score", "DD Extracted", "DD Expected", "DD Error", "DD error_description",
                "DW Score", "DW Extracted", "DW Expected", "DW Error", "DW error_description",
                "AN Score", "AN Extracted", "AN Expected", "AN Missing", "AN TP", "AN FP", "AN FN",
                "AN Extra", "AN Error", "AN error_description", "FinalScore"
            ]
        elif self.dataset_key == "fatura":
            return (
                ["FileName", "DueDate Score", "DueDate Extracted", "DueDate Expected", "DueDate Error",
                 "Total Score", "Total Extracted", "Total Expected", "Total Error", "Missed Extractions"]
                + [f"Item_{i+1}_{field}" for i in range(MAX_ITEMS)
                   for field in ["Name Extracted", "Name Error", "Quantity Extracted", "Quantity Error",
                                 "Price Extracted", "Price Error", "Relation"]]
            )
        elif self.dataset_key == "cord":
            return (
                ["FileName", "Total Score", "Total Extracted", "Total Expected", "Total Error", "Missed Extractions"]
                + [f"Item_{i+1}_{field}" for i in range(MAX_ITEMS)
                   for field in ["Name Extracted", "Name Error", "Price Extracted", "Price Error", "Relation"]]
            )
        else:
            raise ValueError(f"Unknown dataset: {self.dataset_key}")

    def flatten(self, data: dict) -> dict:
        if self.dataset_key == "mio":
            return self._flatten_mio(data)
        elif self.dataset_key == "fatura":
            return self._flatten_fatura(data)
        elif self.dataset_key == "cord":
            return self._flatten_cord(data)
        else:
            raise ValueError(f"Unknown dataset: {self.dataset_key}")

    def _flatten_mio(self, data: dict) -> dict:
        return {
            "FileName":             data["FileName"],
            "ON Score":             data["OrderNumber"]["score"],
            "ON Extracted":         data["OrderNumber"]["extracted"],
            "ON Expected":          data["OrderNumber"]["expected"],
            "ON Error":             data["OrderNumber"]["error"],
            "ON error_description": data["OrderNumber"]["error_description"],
            "DD Score":             data["DeliveryDate"]["score"],
            "DD Extracted":         data["DeliveryDate"]["extracted"],
            "DD Expected":          data["DeliveryDate"]["expected"],
            "DD Error":             data["DeliveryDate"]["error"],
            "DD error_description": data["DeliveryDate"]["error_description"],
            "DW Score":             data["DeliveryWeek"]["score"],
            "DW Extracted":         data["DeliveryWeek"]["extracted"],
            "DW Expected":          data["DeliveryWeek"]["expected"],
            "DW Error":             data["DeliveryWeek"]["error"],
            "DW error_description": data["DeliveryWeek"]["error_description"],
            "AN Score":             data["ArticleNumbers"]["score"],
            "AN Extracted":         data["ArticleNumbers"]["extracted"],
            "AN Expected":          data["ArticleNumbers"]["expected"],
            "AN Missing":           data["ArticleNumbers"]["missing"],
            "AN Extra":             data["ArticleNumbers"]["extra"],
            "AN TP":                data["ArticleNumbers"]["TP"],
            "AN FP":                data["ArticleNumbers"]["FP"],
            "AN FN":                data["ArticleNumbers"]["FN"],
            "AN Error":             data["ArticleNumbers"]["error"],
            "AN error_description": data["ArticleNumbers"]["error_description"],
            "FinalScore":           data["finalScore"]
        }

    def _flatten_fatura(self, data: dict) -> dict:
        row = {
            "FileName":           data["FileName"],
            "DueDate Score":      data["DueDate"]["score"],
            "DueDate Extracted":  data["DueDate"]["extracted"],
            "DueDate Expected":   data["DueDate"]["expected"],
            "DueDate Error":      data["DueDate"]["error"],
            "Total Score":        data["Total"]["score"],
            "Total Extracted":    data["Total"]["extracted"],
            "Total Expected":     data["Total"]["expected"],
            "Total Error":        data["Total"]["error"],
            "Missed Extractions": data["missedExtractions"]
        }
        for i, item in enumerate(data["Items"]):
            row[f"Item_{i+1}_Name Extracted"]     = item["name"]["extracted"]
            row[f"Item_{i+1}_Name Error"]         = item["name"]["error"]
            row[f"Item_{i+1}_Quantity Extracted"] = item["quantity"]["extracted"]
            row[f"Item_{i+1}_Quantity Error"]     = item["quantity"]["error"]
            row[f"Item_{i+1}_Price Extracted"]    = item["price"]["extracted"]
            row[f"Item_{i+1}_Price Error"]        = item["price"]["error"]
            row[f"Item_{i+1}_Relation"]           = item["matching_relation"]
        return row

    def _flatten_cord(self, data: dict) -> dict:
        row = {
            "FileName":           data["FileName"],
            "Total Score":        data["Total"]["score"],
            "Total Extracted":    data["Total"]["extracted"],
            "Total Expected":     data["Total"]["expected"],
            "Total Error":        data["Total"]["error"],
            "Missed Extractions": data["missedExtractions"]
        }
        for i, item in enumerate(data["Items"]):
            row[f"Item_{i+1}_Name Extracted"]  = item["name"]["extracted"]
            row[f"Item_{i+1}_Name Error"]      = item["name"]["error"]
            row[f"Item_{i+1}_Price Extracted"] = item["price"]["extracted"]
            row[f"Item_{i+1}_Price Error"]     = item["price"]["error"]
            row[f"Item_{i+1}_Relation"]        = item["matching_relation"]
        return row

    def add_line(self, data: dict) -> None:
        self.writer.writerow(self.flatten(data))