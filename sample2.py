import json
json_string = "```json\n{\n  \"field1\": {\n    \"type\": \"STRING\",\n    \"nullable\": true,\n    \"generator\": {\n      \"type\": \"random_string\",\n      \"min_length\": 5,\n      \"max_length\": 20,\n      \"characters\": \"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\"\n    }\n  },\n  \"bignumeric_1\": {\n    \"type\": \"BIGNUMERIC\",\n    \"nullable\": true,\n    \"generator\": {\n      \"type\": \"random_number\",\n      \"min\": -99999999999999999999999999.999999999,\n      \"max\": 99999999999999999999999999.999999999,\n      \"precision\": 9\n    }\n  }\n}\n```"
def clean_schema_string(json_string):
    if not isinstance(json_string, str):
        raise TypeError("json_string must be a string")

    cleaned = json_string.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()

        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].lstrip()

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].rstrip()

    return cleaned


json_string = clean_schema_string(json_string)


print(json.loads(json_string))