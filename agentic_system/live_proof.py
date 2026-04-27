import os
import json
import requests

# ===== CONFIG =====
QWEN_URL = "http://127.0.0.1:8000/v1/chat/completions"
CHATGPT_URL = "https://api.openai.com/v1/chat/completions"
CHATGPT_API_KEY = os.getenv("OPENAI_API_KEY")

# ===== QWEN =====
def qwen_generate_task(context):
    payload = {
        "model": "qwen32b",
        "messages": [
            {"role": "system", "content": "Return ONLY JSON. Generate next task."},
            {"role": "user", "content": context}
        ]
    }
    r = requests.post(QWEN_URL, json=payload)
    return json.loads(r.json()["choices"][0]["message"]["content"])

# ===== EXECUTOR =====
def execute_task(task):
    try:
        if task["type"] == "DEVELOP":
            with open(task["file"], "w") as f:
                f.write(task["content"])
            return {"status": "SUCCESS"}

        if task["type"] == "TEST":
            with open(task["file"], "r") as f:
                content = f.read()
            return {"status": "SUCCESS", "content": content}

    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

# ===== CHATGPT VALIDATOR =====
def validate(task, result):
    payload = {
        "model": "gpt-5.3",
        "messages": [
            {
                "role": "system",
                "content": "Strict validator. Respond ONLY JSON: {validation_status, decision, next_task}"
            },
            {
                "role": "user",
                "content": f"Task: {task}\nResult: {result}"
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {CHATGPT_API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(CHATGPT_URL, json=payload, headers=headers)
    return json.loads(r.json()["choices"][0]["message"]["content"])

# ===== LOOP =====
def run():
    context = "Create file proof.txt with content ChatGPT_Control_Test_123 and verify it"

    while True:
        print("\n--- NEW ITERATION ---")

        task = qwen_generate_task(context)
        print("TASK:", task)

        result = execute_task(task)
        print("RESULT:", result)

        decision = validate(task, result)
        print("VALIDATION:", decision)

        if decision.get("decision") == "COMPLETE":
            print("✅ FULL LOOP COMPLETE — SYSTEM IS AGENTIC")
            break

        context = f"{task} -> {result} -> {decision}"

if __name__ == "__main__":
    run()
