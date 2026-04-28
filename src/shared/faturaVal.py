import json
from pathlib import Path
import re

class FaturaValidator:
    def __init__(self, extractedValues, dataset_name: str, validation_folder_path: str | Path, file_path: str | Path):
        self.extractedValues = extractedValues
        self.filename = Path(file_path).stem
        self.score = self.loadScore()
        self.score["FileName"] = self.filename
        self.validation_file_path = Path(validation_folder_path / f"{dataset_name}.json")

        with open(self.validation_file_path, "r") as file:
            self.groundTruth = json.load(file)
            
        self.trueValues = self.find_by_filename()
        self.validateFaturaExtract()

    def get_score(self):
        return self.score

    def find_by_filename(self):
        for doc in self.groundTruth:
            if doc["document_id"] == self.filename:
                return doc
        return None
                    

    def validateFaturaExtract(self):
        self.validateTotal()
        self.validateDate()
        self.validateItems()
        

    #Should be a float, But if its not, lets not crash
    def toFloat(self, value):
        try:
            return float(re.sub(r'[^\d.-]', '', str(value)))  # also strips currency symbols
        except (ValueError, TypeError):
            return None

    def validateTotal(self):    
        extractedTotal = self.extractedValues.get("TotalSum", {}).get("value", None)
        trueTotal = self.trueValues.get("total", None)
        extractedConfidence = self.extractedValues.get("TotalSum", {}).get("confidence", None)
        

        self.score["Total"]["extracted"] = extractedTotal
        self.score["Total"]["expected"]  = trueTotal
        self.score["Total"]["confidence"] = extractedConfidence

        if extractedTotal is None and trueTotal is None:
            self.score["Total"]["error"]             = "TN"
            self.score["Total"]["error_description"] = "Both empty"
            self.score["Total"]["score"]             = 1

        elif extractedTotal is None and trueTotal is not None:
            self.score["Total"]["error"]             = "FN"
            self.score["Total"]["error_description"] = "Nothing extracted"
            self.score["Total"]["score"]             = 0

        elif extractedTotal is not None and trueTotal is None:
            self.score["Total"]["error"]             = "FP"
            self.score["Total"]["error_description"] = "Should be empty"
            self.score["Total"]["score"]             = 0

        elif self.toFloat(extractedTotal) is not None and self.toFloat(extractedTotal) == self.toFloat(trueTotal):
            self.score["Total"]["error"]             = "TP"
            self.score["Total"]["error_description"] = "Correct extraction"
            self.score["Total"]["score"]             = 1

        else:
            self.score["Total"]["error"]             = "FP"
            self.score["Total"]["error_description"] = "Dont match"
            self.score["Total"]["score"]             = 0


    def validateDate(self):     
        extractedDate = self.extractedValues.get("DueDate", {}).get("value") or None
        trueDate      = self.trueValues.get("due_date") or None
        trueDateISO   = self.trueValues.get("DateISO") or None
        extractedConfidence = self.extractedValues.get("DueDate", {}).get("confidence", None)

        self.score["DueDate"]["extracted"] = extractedDate
        self.score["DueDate"]["expected"]  = trueDate, trueDateISO
        self.score["DueDate"]["confidence"] = extractedConfidence 

        if extractedDate is None and trueDate is None:
            self.score["DueDate"]["error"]              = "TN"
            self.score["DueDate"]["error_description"]  = "Both empty"
            self.score["DueDate"]["score"]              = 1

        elif extractedDate is None and trueDate is not None:
            self.score["DueDate"]["error"]              = "FN"
            self.score["DueDate"]["error_description"]  = "Nothing extracted"
            self.score["DueDate"]["score"]              = 0

        elif extractedDate is not None and trueDate is None:
            self.score["DueDate"]["error"]              = "FP"
            self.score["DueDate"]["error_description"]  = "Should be empty"
            self.score["DueDate"]["score"]              = 0

        elif str(extractedDate) == str(trueDate) or str(extractedDate) == str(trueDateISO):
            self.score["DueDate"]["error"]              = "TP"
            self.score["DueDate"]["error_description"]  = "Correct extraction"
            self.score["DueDate"]["score"]              = 1

        else:
            self.score["DueDate"]["error"]              = "FP"
            self.score["DueDate"]["error_description"]  = "Dont match"
            self.score["DueDate"]["score"]              = 0


    def validateItems(self):
        allTrueItems = self.trueValues.get("line_items", [])
        allExtracted = self.extractedValues.get("LineItems", [])
    
        prices = []
        names = []
        quantity = []
        for item in allTrueItems:
            prices.append(item["price"])
            names.append(item["name"])
            quantity.append(item["quantity"])

        for item in allExtracted:
            newItem = self.loadEmptyItem()
            newItem["name"]["extracted"]  = item["Name"]
            newItem["name"]["expected"]  = names

            newItem["price"]["extracted"] = item["Price"]
            newItem["price"]["expected"] = prices 

            newItem["quantity"]["extracted"] = item["Quantity"]
            newItem["quantity"]["expected"] = quantity

            newItem["name"]["confidence"]     = item.get("Name_confidence")
            newItem["price"]["confidence"]    = item.get("Price_confidence")
            newItem["quantity"]["confidence"] = item.get("Quantity_confidence")

            if item["Name"] is None:
                newItem["name"]["error"]             = "FN"
                newItem["name"]["error_description"] = "Nothing extracted"
            elif item["Name"] in names:
                newItem["name"]["error"] = "TP"
                newItem["name"]["error_description"] = "Correct extracted"
            else:
                newItem["name"]["error"] = "FP"
                newItem["name"]["error_description"] = "Wrong extraction"


            if item["Price"] is None:
                newItem["price"]["error"]             = "FN"
                newItem["price"]["error_description"] = "Nothing extracted"
            elif self.toFloat(item["Price"]) in prices:
                newItem["price"]["error"] = "TP"
                newItem["price"]["error_description"] = "Correct extracted"
            else:
                newItem["price"]["error"] = "FP"
                newItem["price"]["error_description"] = "Wrong extraction"

            if item["Quantity"] is None:
                newItem["quantity"]["error"]             = "FN"
                newItem["quantity"]["error_description"] = "Nothing extracted"
            elif self.toFloat(item["Quantity"]) in quantity:
                newItem["quantity"]["error"] = "TP"
                newItem["quantity"]["error_description"] = "Correct extracted"
            else:
                newItem["quantity"]["error"] = "FP"
                newItem["quantity"]["error_description"] = "Wrong extraction"

            self.score["Items"].append(newItem)


            for expectedSet in allTrueItems:
                if str(newItem["name"]["extracted"]) == str(expectedSet["name"]) and \
                    self.toFloat(newItem["quantity"]["extracted"])  == self.toFloat(expectedSet["quantity"]) and \
                    self.toFloat(newItem["price"]["extracted"])     == self.toFloat(expectedSet["price"]):
                        newItem["matching_relation"] = True
                        break
                
        self.score["missedExtractions"] = max(0, len(allTrueItems) - len(allExtracted))

    def loadScore(self):
        emptyScore = {
            "FileName": None,
            "DueDate": {
                "score": 0,
                "extracted": None,
                "expected": None,
                "confidence": None,
                "error": None,
                "error_description": None
            },
            "Total": {
                "score": 0,
                "extracted": None,
                "expected": None,
                "confidence": None,
                "error": None,
                "error_description": None
            },
            "Items": [],   # each entry is one item with its own scores
            "missedExtractions": None, # False Negatives
        }
        return emptyScore

    def loadEmptyItem(self):
        emptyItem = {
            "name": {
                "extracted": None,
                "expected": None,
                "confidence": None,
                "error": None,
                "error_description": None
            },
            "quantity": {
                "extracted": None,
                "expected": None,
                "confidence": None,
                "error": None,
                "error_description": None
            },
            "price": {
                "extracted": None,
                "expected": None,
                "confidence": None,
                "error": None,
                "error_description": None
            },
            "matching_relation": False
        }
        return emptyItem
