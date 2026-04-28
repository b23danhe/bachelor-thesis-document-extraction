schema = {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": False,
  "properties": {
    "OrderNumber": {
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "value": {
            "type": ["string", "null"],
        }
      },
      "required": ["value"]
    },
    "DeliveryDate": {
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "value": {
            "type": ["string", "null"]
        }
      },
      "required": ["value"]
    },
    "DeliveryWeek":{
      "type": "object",
      "additionalProperties": False,
      "properties":{
          "value": {
              "type": ["string", "null"]
          }
      },
      "required": ["value"]
    },
    "ArticleNumbers": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "required": ["OrderNumber", "DeliveryDate", "ArticleNumbers", "DeliveryWeek"]
}

schemaFATURA = {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": False,
  "properties": {
    "DueDate": {
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "value": {
            "type": ["string", "null"],
        }
      },
      "required": ["value"]
    },
    "TotalSum": {
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "value": {
          "type": ["string", "null"]
        }
      },
      "required": ["value"]
    },
    "LineItems": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
          "Name": {
            "type": ["string", "null"]
          },
          "Quantity": {
            "type": ["string", "null"]
          },
          "Price": {
            "type": ["string", "null"]
          }
        },
        "required": ["Name", "Quantity", "Price"]
      }
    }
  },
  "required": ["DueDate", "TotalSum", "LineItems"]
}

schemaCORD = {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": False,
  "properties": {
    "TotalSum": {
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "value": {
          "type": ["string", "null"]
        }
      },
      "required": ["value"]
    },
    "LineItems": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
          "Name": {
            "type": ["string", "null"]
          },
          "Price": {
            "type": ["string", "null"]
          }
        },
        "required": ["Name", "Price"]
      }
    }
  },
  "required": ["TotalSum", "LineItems"]
}