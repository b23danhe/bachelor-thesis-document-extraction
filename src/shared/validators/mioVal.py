from pathlib import Path
from ..validator import Validator


class MioValidator(Validator):

    def __init__(self, validation_file_dir: str | Path):
        super().__init__(validation_file_dir)


    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
    # Score structure
    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

    def loadScore(self) -> dict:
        emptyScore = { # Score output as a dictionary
                "FileName": None,
                "OrderNumber": {
                    "score": 0,
                    "extracted": None,
                    "expected": None,
                    "error": None,
                    "error_description": None 
                },
                "DeliveryDate": {
                    "score": 0,
                    "extracted": None,
                    "expected": None,
                    "error": None,
                    "error_description": None 
                },
                "DeliveryWeek":{
                    "score": 0,
                    "extracted": None,
                    "expected": None,
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

    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
    # Main validation function
    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

    def validateJson(self, inputData: dict, file_path: Path) -> dict:
        jsonScore = self.loadScore()

        file_name = Path(file_path).stem
        jsonScore["FileName"] = file_name

        groundTruth = self.goldenSTD.get(file_name)
        if groundTruth is None:
            for field in ("OrderNumber", "DeliveryDate", "DeliveryWeek", "ArticleNumbers"):
                jsonScore[field]["error"] = "No_reference_filename"
            return jsonScore
        
        self.validateOrderNumber(inputData, groundTruth, jsonScore)
        self.validateArticleNumbers(inputData, groundTruth, jsonScore)
        self.validateDate(inputData, groundTruth, jsonScore)
        self.validateWeekNumber(inputData, groundTruth, jsonScore)

        finalscore = jsonScore["OrderNumber"]["score"] + jsonScore["ArticleNumbers"]["score"]
        if (jsonScore["DeliveryWeek"]["score"] or jsonScore["DeliveyDate"]["score"]) == 1:
            finalscore += 1
        jsonScore["finalScore"] = finalscore

        return jsonScore

    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
    # Field validator functions
    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

    def validateOrderNumber(self, inputData: dict, groundTruth: dict, jsonScore: dict) -> None:
        extractedOrderNr = str(inputData.get("OrderNumber", {}).get("value") or "")
        expectedOrderNr = str(groundTruth.get("OrderNumber") or "")
        supplierOrderNr = str(groundTruth.get("SupplierOrderNumber") or "")

        jsonScore["OrderNumber"]["extracted"] = extractedOrderNr
        jsonScore["OrderNumber"]["expected"]  = expectedOrderNr
            
        if not extractedOrderNr and expectedOrderNr:
            jsonScore["OrderNumber"]["score"] = 0
            jsonScore["OrderNumber"]["error"] = "False Negative"
            jsonScore["OrderNumber"]["error_description"] = "Nothing extracted"
        elif not extractedOrderNr and not expectedOrderNr:
            jsonScore["OrderNumber"]["score"] = 1
            jsonScore["OrderNumber"]["error"] = "True Negative"
            jsonScore["OrderNumber"]["error_description"] = "Both empty"
        elif extractedOrderNr == expectedOrderNr:
            jsonScore["OrderNumber"]["score"] = 1
            jsonScore["OrderNumber"]["error"] = "True Positive"
            jsonScore["OrderNumber"]["error_description"] = "Correct extracted"
        elif supplierOrderNr and extractedOrderNr == supplierOrderNr:
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
        expectedDateISO = groundTruth.get("DeliveryDateISO")
        registrationDate = groundTruth.get("RegistrationDate")

        jsonScore["DeliveryDate"]["extracted"] = extractedDate
        jsonScore["DeliveryDate"]["expected"] = expectedDate, expectedDateISO

        if not extractedDate and expectedDate:
            jsonScore["DeliveryDate"]["score"] = 0
            jsonScore["DeliveryDate"]["error"] = "False Negative"
            jsonScore["DeliveryDate"]["error_description"] = "Nothing extracted"
        elif not extractedDate and not expectedDate:
            jsonScore["DeliveryDate"]["score"] = 1
            jsonScore["DeliveryDate"]["error"] = "True Negative"
            jsonScore["DeliveryDate"]["error_description"] = "Both empty"
        elif extractedDate == expectedDate or extractedDate == expectedDateISO:
            jsonScore["DeliveryDate"]["score"] = 1
            jsonScore["DeliveryDate"]["error"] = "True Positive"
            jsonScore["DeliveryDate"]["error_description"] = "Correct extracted"
        elif registrationDate and extractedDate == registrationDate:
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

        jsonScore["DeliveryWeek"]["extracted"] = extractedWeek
        jsonScore["DeliveryWeek"]["expected"] = expectedWeek

        if not extractedWeek and expectedWeek:
            jsonScore["DeliveryWeek"]["score"] = 0
            jsonScore["DeliveryWeek"]["error"] = "False Negative"
            jsonScore["DeliveryWeek"]["error_description"] = "Nothing extracted"
        elif not extractedWeek and not expectedWeek:
            jsonScore["DeliveryWeek"]["score"]= 1
            jsonScore["DeliveryWeek"]["error"] = "True Negative"
            jsonScore["DeliveryWeek"]["error_description"] = "Both empty"
        elif extractedWeek == expectedWeek:
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
        fn = len(missing)

        jsonScore["ArticleNumbers"]["extracted"] = list(extractedArticles)
        jsonScore["ArticleNumbers"]["expected"] = list(expectedArticles)
        jsonScore["ArticleNumbers"]["missing"] = list(missing)
        jsonScore["ArticleNumbers"]["extra"] = list(extra)
        jsonScore["ArticleNumbers"]["TP"] = tp
        jsonScore["ArticleNumbers"]["FP"] = fp
        jsonScore["ArticleNumbers"]["FN"] = fn
        jsonScore["ArticleNumbers"]["score"] = 1 if fp == 0 and fn == 0 else 0