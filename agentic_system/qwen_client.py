import requests
import json
from task_schema import extract_all_json, normalize_task

class QwenClient:
    def __init__(self, base_url="http://127.0.0.1:11434/v1/chat/completions", model="qwen2.5-coder:32b"):
        self.base_url = base_url
        self.model = model

    def generate_task(self, memory):
        sys_content = "You are an autonomous Agent. You MUST return multiple JSON steps. Each step must be a valid JSON object. Steps should include: file creation, writing content, running script, capturing output.\n\n"
        if hasattr(memory, "get_context"):
            sys_content += memory.get_context()
            
        history = memory.get_qwen_history() if hasattr(memory, "get_qwen_history") else memory
        messages = [{"role": "system", "content": sys_content}] + history
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2
        }
        try:
            response = requests.post(self.base_url, json=payload, timeout=60)
            response.raise_for_status()
            raw_output = response.json()["choices"][0]["message"]["content"]
            print("RAW QWEN OUTPUT:", raw_output)
            
            task_jsons = extract_all_json(raw_output)
            tasks = []
            for t in task_jsons:
                norm_task = normalize_task(t)
                if "type" not in norm_task:
                    print("WARNING: Task normalized with fallback logic")
                print("NORMALIZED TASK:", norm_task)
                tasks.append(norm_task)
                
            if not tasks:
                return [normalize_task({})] # fallback trigger
                
            return tasks
        except Exception as e:
            raise RuntimeError(f"Qwen API error: {e}")
