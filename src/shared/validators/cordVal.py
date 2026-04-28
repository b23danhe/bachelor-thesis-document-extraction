from pathlib import Path
import json
from ..validator import Validator


class CordValidator(Validator):
    """Validator for the Cord dataset.

    Unlike Mio/Fatura, Cord ground truth is stored as individual JSON files
    under cord_v2/test/, one per document. Fields: Total, LineItems.
    """

    def __init__(self, cord_test_dir: str | Path):
        """
        Args:
            cord_test_dir: Path to the cord_v2/test/ directory containing
                           per-document ground truth JSON files.
        """
        self.cord_test_dir = Path(cord_test_dir)
        # Cord doesn't use a single goldenSTD file, so we satisfy the base
        # class without opening a file by setting goldenSTD to None.
        self.goldenSTD = None

    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
    # Score structure
    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

    def loadScore(self) -> dict:
        return {
            "FileName": None,
            "Total": {
                "score": 0,
                "extracted": None,
                "expected": None,
                "error": None,
                "error_description": None,
            },
            "Items": [],
            "missedExtractions": None,
            "finalScore": 0,
        }

    def _loadEmptyItem(self) -> dict:
        return {
            "name": {
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
    # Ground truth loader (per-file, from cord_v2/test/)
    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

    def _loadGroundTruth(self, file_path: Path) -> dict:
        gt_path = self.cord_test_dir / (Path(file_path).stem + ".json")
        with open(gt_path) as f:
            raw = json.load(f)

        groundTruth = {"total": None, "items": []}
        groundTruth["total"] = raw["gt_parse"]["total"]["total_price"]

        allItems = raw["gt_parse"]["menu"]
        if isinstance(allItems, list):
            for item in allItems:
                groundTruth["items"].append({"name": item["nm"], "price": item["price"]})
        else:
            groundTruth["items"].append({"name": allItems["nm"], "price": allItems["price"]})

        return groundTruth

    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
    # Main validation function
    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

    def validateJson(self, inputData: dict, file_path: Path) -> dict:
        jsonScore = self.loadScore()
        jsonScore["FileName"] = Path(file_path).stem

        groundTruth = self._loadGroundTruth(file_path)

        self.validateTotal(inputData, groundTruth, jsonScore)
        self.validateItems(inputData, groundTruth, jsonScore)

        jsonScore["finalScore"] = jsonScore["Total"]["score"]

        return jsonScore

    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
    # Field validator functions
    # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

    def validateTotal(self, inputData: dict, groundTruth: dict, jsonScore: dict) -> None:
        extractedTotal = inputData.get("TotalSum", {}).get("value")
        trueTotal      = groundTruth["total"]

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
        elif extractedTotal == trueTotal:
            jsonScore["Total"]["score"]             = 1
            jsonScore["Total"]["error"]             = "TP"
            jsonScore["Total"]["error_description"] = "Correct extraction"
        else:
            jsonScore["Total"]["score"]             = 0
            jsonScore["Total"]["error"]             = "FP"
            jsonScore["Total"]["error_description"] = "Dont match"

    def validateItems(self, inputData: dict, groundTruth: dict, jsonScore: dict) -> None:
        allTrueItems = groundTruth.get("items", [])
        allExtracted = inputData.get("LineItems", [])

        # Work on copies so we can remove matched entries to prevent double-matching
        remainingNames  = [item["name"]  for item in allTrueItems]
        remainingPrices = [item["price"] for item in allTrueItems]

        # Keep originals for the "expected" display field
        expectedNames  = remainingNames.copy()
        expectedPrices = remainingPrices.copy()

        for item in allExtracted:
            newItem = self._loadEmptyItem()
            newItem["name"]["extracted"]  = item["name"]
            newItem["name"]["expected"]   = expectedNames
            newItem["price"]["extracted"] = item["price"]
            newItem["price"]["expected"]  = expectedPrices

            if item["name"] in remainingNames:
                newItem["name"]["error"]             = "TP"
                newItem["name"]["error_description"] = "Correct extracted"
                remainingNames.remove(item["name"])
            else:
                newItem["name"]["error"]             = "FP"
                newItem["name"]["error_description"] = "Wrong extraction"

            if item["price"] in remainingPrices:
                newItem["price"]["error"]             = "TP"
                newItem["price"]["error_description"] = "Correct extracted"
                remainingPrices.remove(item["price"])
            else:
                newItem["price"]["error"]             = "FP"
                newItem["price"]["error_description"] = "Wrong extraction"

            jsonScore["Items"].append(newItem)

        # Check full row match (name + price together)
        for newItem in jsonScore["Items"]:
            for expectedSet in allTrueItems:
                if (
                    newItem["name"]["extracted"]  == expectedSet["name"]
                    and newItem["price"]["extracted"] == expectedSet["price"]
                ):
                    newItem["matching_relation"] = True
                    break

        jsonScore["missedExtractions"] = max(0, len(allTrueItems) - len(allExtracted))