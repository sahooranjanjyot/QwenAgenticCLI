import os
import requests
import json

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def clean_json_response(text):
    text = text.strip()

    # Remove markdown ```json blocks
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    
    # Remove ending ```
    text = text.replace("```", "").strip()

    return text

def chatgpt_validate(validation_payload):
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
You are the Supervisor.
The worker agent performed an action. Review the execution and output.

Payload:
{json.dumps(validation_payload, default=str, indent=2)}

Return ONLY a strictly formatted JSON object. No extra text, no markdown.
{{
  "decision": "SUCCESS" or "FAIL",
  "feedback": "exact fix instructions"
}}
"""
        payload = {
            "model": "gpt-4-turbo-preview",
            "messages": [{"role": "system", "content": prompt}],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }

        if not OPENAI_API_KEY:
            return {"decision": "SUCCESS" if validation_payload.get("health_ok") else "FAIL", "feedback": "Fallback key missing."}

        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        
        content = resp.json()["choices"][0]["message"]["content"]
        content = clean_json_response(content)
        
        try:
            return json.loads(content)
        except:
            return {"decision": "FAIL", "feedback": "Supervisor returned invalid JSON."}

    except Exception as e:
        return {"decision": "FAIL", "feedback": f"Validator API error: {str(e)}"}

def check_compliance(action, governance_feedback=None):
    # Temporary minimal compliance pass-through
    return {
        "compliant": True,
        "decision": "PASS",
        "failure_type": None,
        "reason": "Default allow (self-healing mode)",
        "blocking_rule": None
    }
