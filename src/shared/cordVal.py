import json
from pathlib import Path
import re

def loadScore():
    emptyScore = {
        "FileName": None,
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
        "finalScore": 0
    }
    return emptyScore

def loadEmptyItem():
    emptyItem = {
        "name": {
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

    #Should be a float, But if its not, lets not crash
def toFloat(value):
        try:
            return float(re.sub(r'[^\d.-]', '', str(value)))  # also strips currency symbols
        except (ValueError, TypeError):
            return None

def makeTruthFromFile(validation_folder_path, filename: Path):
    groundTruth = {
        "filename": None,
        "total": 0,
        "items": []
    }

    filename = filename.stem + ".json"
    path = validation_folder_path / filename
    with open(path) as f:
        truth = json.load(f)

    allItems = truth.get("gt_parse", {}).get("menu", [])

    if isinstance(allItems, list):
        for item in allItems:
            name = item.get("nm")
            price = item.get("price")
            groundTruth["items"].append({"name": name, "price": price})
    else:
        name = allItems["nm"]
        price = allItems["price"]
        groundTruth["items"].append({"name": name, "price": price})

    groundTruth["total"] = truth.get("gt_parse", {}).get("total", {}).get("total_price", 0)

    return groundTruth

def validateCordExtract(extractedValues: dict, validation_folder_path: str | Path, filename: Path) -> dict:
    
    finalScore = loadScore()
    finalScore["FileName"] = str(filename)
    truth = makeTruthFromFile(validation_folder_path, filename)

    validateItems(extractedValues, truth, finalScore)
    validateTotal(extractedValues, truth, finalScore)
    
    return finalScore

def validateTotal(extractedValues, truthValues, finalScore):
    extractedTotal = extractedValues.get("TotalSum", {}).get("value", None)
    extractedConfidence = extractedValues.get("TotalSum", {}).get("confidence", None)
    trueTotal = truthValues["total"]
    finalScore["Total"]["extracted"] = extractedTotal
    finalScore["Total"]["expected"]  = trueTotal
    finalScore["Total"]["confidence"] = extractedConfidence

    if extractedTotal is None and trueTotal is None:
        finalScore["Total"]["error"]             = "TN"
        finalScore["Total"]["error_description"] = "Both empty"
        finalScore["Total"]["score"]             = 1

    elif extractedTotal is None and trueTotal is not None:
        finalScore["Total"]["error"]             = "FN"
        finalScore["Total"]["error_description"] = "Nothing extracted"
        finalScore["Total"]["score"]             = 0

    elif extractedTotal is not None and trueTotal is None:
        finalScore["Total"]["error"]             = "FP"
        finalScore["Total"]["error_description"] = "Should be empty"
        finalScore["Total"]["score"]             = 0

    elif toFloat(extractedTotal) == toFloat(trueTotal):
        finalScore["Total"]["error"]             = "TP"
        finalScore["Total"]["error_description"] = "Correct extraction"
        finalScore["Total"]["score"]             = 1

    else:
        finalScore["Total"]["error"]             = "FP"
        finalScore["Total"]["error_description"] = "Dont match"
        finalScore["Total"]["score"]  

def validateItems(extractedValues, truthValues, finalScore):
    allTrueItems = truthValues.get("items", [])
    allExtracted = extractedValues.get("LineItems", [])
 
    prices = []
    names = []
    for item in allTrueItems:
        prices.append(item["price"])
        names.append(item["name"])

    # As I remove each from prices and names later to not have double maches possible
    # but we still need them for expected later
    pricesExpected = prices.copy()
    namesExpected = names.copy() 

    for item in allExtracted:
        newItem = loadEmptyItem()
        newItem["name"]["extracted"]  = item["Name"]
        newItem["name"]["expected"]  = namesExpected
        newItem["name"]["confidence"] = item.get("Name_confidence")
        newItem["price"]["extracted"] = item["Price"]
        newItem["price"]["expected"] = pricesExpected 
        newItem["price"]["confidence"] = item.get("Price_confidence")


        if item["Name"] in names:
            newItem["name"]["error"] = "TP"
            newItem["name"]["error_description"] = "Correct extracted"
        else:
            newItem["name"]["error"] = "FP"
            newItem["name"]["error_description"] = "Wrong extraction"

        if toFloat(item["Price"]) in [toFloat(p) for p in prices]:
            newItem["price"]["error"] = "TP"
            newItem["price"]["error_description"] = "Correct extracted"
        else:
            newItem["price"]["error"] = "FP"
            newItem["price"]["error_description"] = "Wrong extraction"

        finalScore["Items"].append(newItem)


    for newItem in finalScore["Items"]: 
        for expectedSet in allTrueItems:
            if newItem["name"]["extracted"] == expectedSet["name"] and \
            newItem["price"]["extracted"] == expectedSet["price"]:
                newItem["matching_relation"] = True
                break
            
    for newItem in finalScore["Items"]: 
        for expectedSet in allTrueItems:
            name_match = str(newItem["name"]["extracted"]).strip() == str(expectedSet["name"]).strip()
            price_match = toFloat(newItem["price"]["extracted"]) == toFloat(expectedSet["price"])
            if name_match and price_match:
                newItem["matching_relation"] = True
                break

    
    finalScore["missedExtractions"] = max(0, len(allTrueItems) - len(allExtracted))

