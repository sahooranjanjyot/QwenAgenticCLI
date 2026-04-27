import requests
import json
import os
import sys

CHATGPT_URL = "https://api.openai.com/v1/chat/completions"

def chatgpt_validate(goal, memory, workspace_dir="workspace"):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-xxxxxxxx"):
        return {"decision": "FAIL", "reason": "INVALID API KEY"}
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # gather files
    files = []
    if os.path.exists(workspace_dir):
        files = os.listdir(workspace_dir)
        
    context = {
        "goal": goal,
        "files_in_workspace": files,
        "execution_summary": memory.get_messages(limit=10)
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the final audit gate for an autonomous workflow.\n"
                    "You MUST respond ONLY in JSON.\n"
                    "Format:\n"
                    "{\n  \"decision\": \"COMPLETE | FIX\",\n  \"reason\": \"Explanation of missing files or failed test assertions if FIX\"\n}\n"
                    "Rules: Only output COMPLETE if the goal is verifiably achieved by the contents of files_in_workspace and execution_summary."
                )
            },
            {
                "role": "user",
                "content": json.dumps(context)
            }
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"}
    }

    try:
        r = requests.post(CHATGPT_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        return {"decision": "FAIL", "reason": str(e)}
