import json

def extract_action(raw_text):
    raw_text = raw_text.strip()

    # Remove markdown wrappers if present
    if raw_text.startswith("```"):
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    # Try parsing the whole string first
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, list) and len(parsed) > 0:
            for item in parsed:
                if isinstance(item, dict) and ("action_type" in item or "action" in item):
                    return item
        elif isinstance(parsed, dict) and ("action_type" in parsed or "action" in parsed):
            return parsed
    except Exception:
        pass

    decoder = json.JSONDecoder()
    best_obj = None

    for i, ch in enumerate(raw_text):
        if ch != "{":
            continue

        try:
            obj, end = decoder.raw_decode(raw_text[i:])
            if isinstance(obj, dict) and ("action_type" in obj or "action" in obj):
                best_obj = obj
                break
        except Exception:
            continue

    if not best_obj:
        raise ValueError(f"No valid Qwen action JSON found in output: {raw_text}")

    return best_obj
