
# Perfect prompt
PERFECT = """
      Extract the desired information from this order confirmation.
      The desired information is the receiver’s order number, the article number of every purchased item and the date or week that the order is set to be delivered.
      You are an information extraction engine.
      Return a SINGLE JSON object that conforms EXACTLY to the JSON Schema defined in the SCHEMA variable.
      FOLLOW THE SCHEMA!
      The delivery date or week should always be within the time span of the coming six months.

      """.strip()

# Zero shot
ZEROSHOT = """
      Extract the receiver's order number, article number and delivery date or week and return a JSON object that conforms to the JSON Schema defined in the variable SCHEMA.
      """.strip()

ZEROSHOTFATURA = """
      Extract the due date, the sum total, and the name, quantity, and price for every article, and return a JSON object that conforms to the JSON Schema defined in the variable SCHEMA.
      """.strip()

ZEROSHOTCORD = """
      Extract the sum total, and the name and price for every article, and return a JSON object that conforms to the JSON Schema defined in the variable SCHEMA.
      """.strip()