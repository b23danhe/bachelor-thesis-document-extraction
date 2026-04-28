import json
from pathlib import Path
from ..validator import Validator

def _toFloat(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

class FaturaValidator(Validator):

    def __init__(self, validation_file_dir: str | Path):
        super().__init__(validation_file_dir)

    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
    # Score structure
    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

    def loadScore(self) -> dict:
        return {
            "FileName": None,
            "DueDate": {
                "score": 0,
                "extracted": None,
                "expected": None,
                "error": None,
                "error_description": None,
            },
            "Total": {
                "score": 0,
                "extracted": None,
                "expected": None,
                "error": None,
                "error_description": None,
            },
            "Items": [],
            "missedExtractions": None,
        }

    def _loadEmptyItem(self) -> dict:
        return {
            "name": {
                "extracted": None,
                "expected": None,
                "error": None,
                "error_description": None,
            },
            "quantity": {
                "extracted": None,
                "expected": None,
                "error": None,
                "error_description": None,
            },
            "price": {
                "extracted": None,
                "expected": None,
                "error": None,
                "error_description": None,
            },
            "matching_relation": False,
        }

    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
    # Main validation function
    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

    def validateJson(self, inputData: dict, file_path: Path) -> dict:
        jsonScore = self.loadScore()

        file_name = Path(file_path).stem
        jsonScore["FileName"] = file_name

        # Fatura ground truth is a list of dicts keyed by "document_id"
        groundTruth = next(
            (doc for doc in self.goldenSTD if doc.get("document_id") == file_name),
            None,
        )
        if groundTruth is None:
            for field in ("DueDate", "Total"):
                jsonScore[field]["error"] = "No_reference_filename"
            return jsonScore

        self.validateDate(inputData, groundTruth, jsonScore)
        self.validateTotal(inputData, groundTruth, jsonScore)
        self.validateItems(inputData, groundTruth, jsonScore)

        return jsonScore

    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
    # Field validator functions
    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-


    def validateTotal(self, inputData: dict, groundTruth: dict, jsonScore: dict) -> None:
        extractedTotal = inputData.get("TotalSum", {}).get("value")
        trueTotal      = groundTruth.get("total")

        jsonScore["Total"]["extracted"] = extractedTotal
        jsonScore["Total"]["expected"]  = trueTotal

        if extractedTotal is None and trueTotal is None:
            jsonScore["Total"]["score"]             = 1
            jsonScore["Total"]["error"]             = "TN"
            jsonScore["Total"]["error_description"] = "Both empty"
        elif extractedTotal is None:
            jsonScore["Total"]["score"]             = 0
            jsonScore["Total"]["error"]             = "FN"
            jsonScore["Total"]["error_description"] = "Nothing extracted"
        elif trueTotal is None:
            jsonScore["Total"]["score"]             = 0
            jsonScore["Total"]["error"]             = "FP"
            jsonScore["Total"]["error_description"] = "Should be empty"
        elif _toFloat(extractedTotal) == _toFloat(trueTotal):
            jsonScore["Total"]["score"]             = 1
            jsonScore["Total"]["error"]             = "TP"
            jsonScore["Total"]["error_description"] = "Correct extraction"
        else:
            jsonScore["Total"]["score"]             = 0
            jsonScore["Total"]["error"]             = "FP"
            jsonScore["Total"]["error_description"] = "Dont match"

    def validateDate(self, inputData: dict, groundTruth: dict, jsonScore: dict) -> None:
        extractedDate = inputData.get("DueDate", {}).get("value") or None
        trueDate      = groundTruth.get("due_date") or None
        trueDateISO   = groundTruth.get("DateISO") or None

        jsonScore["DueDate"]["extracted"] = extractedDate
        jsonScore["DueDate"]["expected"]  = (trueDate, trueDateISO)

        if extractedDate is None and trueDate is None:
            jsonScore["DueDate"]["score"]             = 1
            jsonScore["DueDate"]["error"]             = "TN"
            jsonScore["DueDate"]["error_description"] = "Both empty"
        elif extractedDate is None:
            jsonScore["DueDate"]["score"]             = 0
            jsonScore["DueDate"]["error"]             = "FN"
            jsonScore["DueDate"]["error_description"] = "Nothing extracted"
        elif trueDate is None:
            jsonScore["DueDate"]["score"]             = 0
            jsonScore["DueDate"]["error"]             = "FP"
            jsonScore["DueDate"]["error_description"] = "Should be empty"
        elif str(extractedDate) in (str(trueDate), str(trueDateISO)):
            jsonScore["DueDate"]["score"]             = 1
            jsonScore["DueDate"]["error"]             = "TP"
            jsonScore["DueDate"]["error_description"] = "Correct extraction"
        else:
            jsonScore["DueDate"]["score"]             = 0
            jsonScore["DueDate"]["error"]             = "FP"
            jsonScore["DueDate"]["error_description"] = "Dont match"

    def validateItems(self, inputData: dict, groundTruth: dict, jsonScore: dict) -> None:
        allTrueItems  = groundTruth.get("line_items", [])
        allExtracted  = inputData.get("LineItems", [])

        trueNames     = [item["name"]     for item in allTrueItems]
        truePrices    = [item["price"]    for item in allTrueItems]
        trueQuantities = [item["quantity"] for item in allTrueItems]

        for item in allExtracted:
            newItem = self._loadEmptyItem()

            newItem["name"]["extracted"]     = item["name"]
            newItem["name"]["expected"]      = trueNames
            newItem["price"]["extracted"]    = item["price"]
            newItem["price"]["expected"]     = truePrices
            newItem["quantity"]["extracted"] = item["quantity"]
            newItem["quantity"]["expected"]  = trueQuantities

            if item["name"] is None:
                newItem["name"]["error"]             = "FN"
                newItem["name"]["error_description"] = "Nothing extracted"
            elif item["name"] in trueNames:
                newItem["name"]["error"]             = "TP"
                newItem["name"]["error_description"] = "Correct extracted"
            else:
                newItem["name"]["error"]             = "FP"
                newItem["name"]["error_description"] = "Wrong extraction"

            if item["price"] is None:
                newItem["price"]["error"]             = "FN"
                newItem["price"]["error_description"] = "Nothing extracted"
            elif self._toFloat(item["price"]) in truePrices:
                newItem["price"]["error"]             = "TP"
                newItem["price"]["error_description"] = "Correct extracted"
            else:
                newItem["price"]["error"]             = "FP"
                newItem["price"]["error_description"] = "Wrong extraction"

            if item["quantity"] is None:
                newItem["quantity"]["error"]             = "FN"
                newItem["quantity"]["error_description"] = "Nothing extracted"
            elif self._toFloat(item["quantity"]) in trueQuantities:
                newItem["quantity"]["error"]             = "TP"
                newItem["quantity"]["error_description"] = "Correct extracted"
            else:
                newItem["quantity"]["error"]             = "FP"
                newItem["quantity"]["error_description"] = "Wrong extraction"

            # Check if the full item (name + quantity + price) matches any ground-truth row
            for expectedSet in allTrueItems:
                if (
                    str(newItem["name"]["extracted"]) == str(expectedSet["name"])
                    and _toFloat(newItem["quantity"]["extracted"]) == _toFloat(expectedSet["quantity"])
                    and _toFloat(newItem["price"]["extracted"])    == _toFloat(expectedSet["price"])
                ):
                    newItem["matching_relation"] = True
                    break

            jsonScore["Items"].append(newItem)

        jsonScore["missedExtractions"] = max(0, len(allTrueItems) - len(allExtracted))