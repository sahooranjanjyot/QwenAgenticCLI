import json

def extract_action(raw_text):
    raw_text = raw_text.strip()

    # Remove markdown wrappers if present
    if raw_text.startswith("```"):
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    decoder = json.JSONDecoder()

    best_obj = None

    for i, ch in enumerate(raw_text):
        if ch != "{":
            continue

        try:
            obj, end = decoder.raw_decode(raw_text[i:])

            # Only accept real Qwen action objects
            if isinstance(obj, dict) and "action_type" in obj:
                best_obj = obj
                break

        except Exception:
            continue

    if not best_obj:
        raise ValueError(f"No valid Qwen action JSON found in output: {raw_text}")

    return best_obj
