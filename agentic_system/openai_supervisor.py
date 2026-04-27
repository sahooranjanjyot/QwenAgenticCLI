import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def review_with_openai(goal, action, result):
    print("🔥 OPENAI SUPERVISOR CALLED")

    prompt = f"""
You are a STRICT agent workflow validator.

You must decide if the CURRENT ACTION is VALID — not whether the task is complete.

Return ONLY JSON:
{{
  "decision": "PASS" or "FAIL",
  "feedback": "what is wrong if FAIL"
}}

RULES:
- READ_FILE is ALWAYS VALID
- PATCH_CODE is VALID if modifying existing file
- WRITE_FILE is INVALID if file already exists
- RUN_COMMAND is VALID if meaningful
- Repeating same action without progress = FAIL

GOAL:
{goal}

ACTION:
{action}

RESULT:
{result}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
