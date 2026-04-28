import json
from pathlib import Path
import pandas as pd
from datetime import date, datetime
#from functools import lru_cache


class Validator:
    def __init__(self, validation_file_dir: str | Path, dataset_name: str):

        self.validation_file_path = validation_file_dir / f"{dataset_name}.json"
        with open(self.validation_file_path, "r") as file:
            self.goldenSTD: dict = json.load(file)
        
    def loadScore(self):
        emptyScore = { # Score output as a dictionary
            "FileName": None,
            "OrderNumber": {
                "score": 0,
                "extracted": None,
                "expected": None,
                "confidence": None,
                "error": None,
                "error_description": None 
            },
            "DeliveryDate": {
                "score": 0,
                "extracted": None,
                "expected": None,
                "confidence": None,
                "error": None,
                "error_description": None 
            },
            "DeliveryWeek":{
                "score": 0,
                "extracted": None,
                "expected": None,
                "confidence": None,
                "error": None,
                "error_description": None 
            },
            "ArticleNumbers": {
                "score": 0,
                "extracted": [],
                "expected": [],
                "missing": [],    # in expected but not in extracted
                "extra": [],
                "TP": None,
                "FP": None,
                "FN": None,    # in extracted but not in expected
                "error": None,
                "error_description": None    
            },
            "finalScore": 0
        }
        return emptyScore
    

    def validateJson(self, inputData: dict, pdf_path: Path) -> dict:
        # Load the ground truth data
        jsonScore = self.loadScore()

        # Use the PDF filename (without extension) as the key to find the corresponding ground truth data
        pdf_name = Path(pdf_path).stem
        jsonScore["FileName"] = pdf_name

        groundTruth = self.goldenSTD.get(pdf_name)
        if groundTruth is None:
            # No ground-truth mapping for this file -> return a score object without crashing
            jsonScore["OrderNumber"]["error"] = "No_reference_filename"
            jsonScore["DeliveryDate"]["error"] = "No_reference_filename"
            jsonScore["DeliveryWeek"]["error"] = "No_reference_filename"
            jsonScore["ArticleNumbers"]["error"] = "No_reference_filename"
            return jsonScore

        # Validate each field and populate the jsonScore dictionary
        self.validateOrderNumber(inputData, groundTruth, jsonScore)
        self.validateArticleNumbers(inputData, groundTruth, jsonScore)
        self.validateDate(inputData, groundTruth, jsonScore)
        self.validateWeekNumber(inputData, groundTruth, jsonScore)

        # Calculate a final score
        finalscore = 0
        finalscore += jsonScore["OrderNumber"]["score"]
        finalscore += jsonScore["ArticleNumbers"]["score"]
        if (jsonScore["DeliveryWeek"]["score"] or jsonScore["DeliveryDate"]["score"]) == 1:
            finalscore +=1
        jsonScore["finalScore"] = finalscore

        return jsonScore
        

    def validateOrderNumber(self, inputData: dict, groundTruth: dict, jsonScore: dict) -> None:
        extractedOrderNr = inputData.get("OrderNumber", {}).get("value") or ""
        expectedOrderNr = groundTruth.get("OrderNumber") or ""
        supplierOrderNr = groundTruth.get("SupplierOrderNumber") or ""
        extractedConfidence = inputData.get("OrderNumber", {}).get("confidence", None)

        jsonScore["OrderNumber"]["extracted"] = extractedOrderNr
        jsonScore["OrderNumber"]["expected"]  = expectedOrderNr
        jsonScore["OrderNumber"]["confidence"] = extractedConfidence
        
        if not extractedOrderNr and expectedOrderNr:
            jsonScore["OrderNumber"]["score"] = 0
            jsonScore["OrderNumber"]["error"] = "False Negative"
            jsonScore["OrderNumber"]["error_description"] = "Nothing extracted"
        elif not extractedOrderNr and not expectedOrderNr:
            jsonScore["OrderNumber"]["score"] = 1
            jsonScore["OrderNumber"]["error"] = "True Negative"
            jsonScore["OrderNumber"]["error_description"] = "Both empty"
        elif str(extractedOrderNr) == str(expectedOrderNr):
            jsonScore["OrderNumber"]["score"] = 1
            jsonScore["OrderNumber"]["error"] = "True Positive"
            jsonScore["OrderNumber"]["error_description"] = "Correct extracted"
        elif supplierOrderNr and str(extractedOrderNr) == str(supplierOrderNr):
            jsonScore["OrderNumber"]["score"] = 0
            jsonScore["OrderNumber"]["error"] = "False Positive"
            jsonScore["OrderNumber"]["error_description"] = "Grabbed Supplier OrderNumber"
        elif extractedOrderNr and not expectedOrderNr:
            jsonScore["OrderNumber"]["score"] = 0
            jsonScore["OrderNumber"]["error"] = "False Positive"
            jsonScore["OrderNumber"]["error_description"] = "Should be empty"
        else:
            # Both has value but they don't match
            jsonScore["OrderNumber"]["score"] = 0
            jsonScore["OrderNumber"]["error"] = "False Positive"
            jsonScore["OrderNumber"]["error_description"] = "Dont match"


    def validateDate(self, inputData: dict, groundTruth: dict, jsonScore: dict) -> None:
        extractedDate = inputData.get("DeliveryDate", {}).get("value")
        expectedDate = groundTruth.get("DeliveryDate")
        expectedDateISO = groundTruth.get("DateISO")
        registrationDate = groundTruth.get("RegistrationDate")
        extractedConfidence = inputData.get("DeliveryDate", {}).get("confidence", None)
 
        jsonScore["DeliveryDate"]["extracted"] = extractedDate
        jsonScore["DeliveryDate"]["expected"] = expectedDate, expectedDateISO
        jsonScore["DeliveryDate"]["confidence"] = extractedConfidence 
        if not extractedDate and expectedDate:
            jsonScore["DeliveryDate"]["score"] = 0
            jsonScore["DeliveryDate"]["error"] = "False Negativ"
            jsonScore["DeliveryDate"]["error_description"] = "Nothing extracted"
        elif not extractedDate and not expectedDate:
            jsonScore["DeliveryDate"]["score"] = 1
            jsonScore["DeliveryDate"]["error"] = "True Negativ"
            jsonScore["DeliveryDate"]["error_description"] = "Both empty"
        elif str(extractedDate) == str(expectedDate) or str(extractedDate) == str(expectedDateISO):
            jsonScore["DeliveryDate"]["score"] = 1
            jsonScore["DeliveryDate"]["error"] = "True Positive"
            jsonScore["DeliveryDate"]["error_description"] = "Correct extracted"
        elif registrationDate and str(extractedDate) == str(registrationDate):
            jsonScore["DeliveryDate"]["score"] = 0
            jsonScore["DeliveryDate"]["error"] = "False Positive"
            jsonScore["DeliveryDate"]["error_description"] = "Grabbed Registration"
        elif extractedDate and not expectedDate:
            jsonScore["DeliveryDate"]["score"] = 0
            jsonScore["DeliveryDate"]["error"] = "False Positive"
            jsonScore["DeliveryDate"]["error_description"] = "Should be empty"
        else:
            # Both has value but they don't match
            jsonScore["DeliveryDate"]["score"] = 0
            jsonScore["DeliveryDate"]["error"] = "False Positive" 
            jsonScore["DeliveryDate"]["error_description"] = "Dont match"


    def validateWeekNumber(self, inputData: dict, groundTruth: dict, jsonScore: dict) -> None:
        extractedWeek = inputData.get("DeliveryWeek", {}).get("value")
        expectedWeek = groundTruth.get("DeliveryWeek")
        extractedConfidence = inputData.get("DeliveryWeek", {}).get("confidence", None)

        # Removed Failed fast on delivery week
        # True negative score point or not?

        jsonScore["DeliveryWeek"]["extracted"] = extractedWeek
        jsonScore["DeliveryWeek"]["expected"] = expectedWeek
        jsonScore["DeliveryWeek"]["confidence"] = extractedConfidence

        if not extractedWeek and expectedWeek:
            jsonScore["DeliveryWeek"]["score"] = 0
            jsonScore["DeliveryWeek"]["error"] = "False Negativ"
            jsonScore["DeliveryWeek"]["error_description"] = "Nothing extracted"
        elif not extractedWeek and not expectedWeek:
            jsonScore["DeliveryWeek"]["score"]= 1
            jsonScore["DeliveryWeek"]["error"] = "True Negativ"
            jsonScore["DeliveryWeek"]["error_description"] = "Both empty"
        elif str(extractedWeek) == str(expectedWeek):
            jsonScore["DeliveryWeek"]["score"] = 1
            jsonScore["DeliveryWeek"]["error"] = "True Positive"
            jsonScore["DeliveryWeek"]["error_description"] = "Correct extraction"
        elif extractedWeek and not expectedWeek:
            jsonScore["DeliveryWeek"]["score"] = 0
            jsonScore["DeliveryWeek"]["error"] = "False Positive"
            jsonScore["DeliveryWeek"]["error_description"] = "Should be empty"
        else:
            # Both has value but they don't match
            jsonScore["DeliveryWeek"]["score"] = 0
            jsonScore["DeliveryWeek"]["error"] = "False Positive"
            jsonScore["DeliveryWeek"]["error_description"]  = "Dont match"


    # Redundant logic of Supplier article number with planned ground truth change
    def validateArticleNumbers(self, inputData: dict, groundTruth: dict, jsonScore: dict) -> None:
        # Get the sets of article numbers from both input and ground truth, ignoring empty values
        expectedArticles = set()
        for articles in groundTruth.get("ArticleNumbers", []):
            expectedArticles.add(str(articles))
            
        extractedArticles = set()
        for article in inputData.get("ArticleNumbers", []):
            extractedArticles.add(str(article))

        # Calculate missing and extra article numbers
        matched = extractedArticles & expectedArticles
        missing = expectedArticles - extractedArticles
        extra = extractedArticles - expectedArticles

        tp = len(matched)
        fp = len(extra)
        fn = max(0, len(missing-extra)) # To catch when expected is more then extracted

        jsonScore["ArticleNumbers"]["extracted"] = list(extractedArticles)
        jsonScore["ArticleNumbers"]["expected"] = list(expectedArticles)
        jsonScore["ArticleNumbers"]["missing"] = list(missing)
        jsonScore["ArticleNumbers"]["extra"] = list(extra)
        jsonScore["ArticleNumbers"]["TP"] = tp
        jsonScore["ArticleNumbers"]["FP"] = fp
        jsonScore["ArticleNumbers"]["FN"] = fn
        jsonScore["ArticleNumbers"]["score"] = 1 if fp == 0 and fn == 0 else 0