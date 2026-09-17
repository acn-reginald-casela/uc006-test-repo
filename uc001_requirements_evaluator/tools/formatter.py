import json

def format_to_readable(items: list[dict]) -> str:
    """
    Render a list of criterion dicts as a human-readable block of text,
    one criterion per paragraph. Only "name", "description", "fail_example",
    and "pass_example" are used from each dict -- other fields (e.g.
    "weight", "pass_threshold") are ignored.
    """
    blocks = []
    for item in items:
        blocks.append(
            f"- {item.get('name', '')}: {item.get('description', '')}\n"
            f"  Fail example: {item.get('fail_example', '')}\n"
            f"  Pass example: {item.get('pass_example', '')}"
        )
    return "\n\n".join(blocks)

def clean_json_string(json_string):
    if not isinstance(json_string, str):
        print(f"Can't convert to json_string:\n", json_string)
        raise TypeError("json_string must be a string")

    start = json_string.find("[")
    end = json_string.rfind("]")
    if start == -1 or end == -1:
        print(f"Can't convert to json_string:\n", json_string)
        raise ValueError("No JSON array found in json_string")

    cleaned = json_string[start:end + 1]
    return json.loads(cleaned)