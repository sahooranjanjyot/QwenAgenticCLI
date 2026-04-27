import os
import sys
import json
import time
import socket
import threading
import logging
import subprocess

from qwen_client import QwenClient
from workspace_manager import WorkspaceManager
from executor import Executor
from validator import call_chatgpt
from memory import Memory
from task_schema import normalize_task

logging.basicConfig(
    filename=f"{os.path.dirname(__file__)}/system.log",
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def is_qwen_running(host="127.0.0.1", port=11434):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(2)
        return s.connect_ex((host, port)) == 0

def start_qwen_server():
    logging.info("Starting Ollama Server...")
    cmd = "ollama serve &"
    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5) 

def health_check_daemon():
    while True:
        if not is_qwen_running():
            start_qwen_server()
        time.sleep(10)

def start_daemons():
    t = threading.Thread(target=health_check_daemon, daemon=True)
    t.start()
    return t

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY or API_KEY.startswith("sk-xxxxxxxx"):
    print("❌ INVALID API KEY — STOP")
    sys.exit(1)

def run_autonomous_loop():
    print("\nAUTONOMOUS AGENT STARTED — CHATGPT GOVERNANCE ACTIVE")
    
    qwen = QwenClient()
    workspace = WorkspaceManager("workspace")
    executor = Executor(workspace)
    memory = Memory()
    
    goal = "Create a Python file math_utils.py with a function add(a, b) that returns their sum. Create another file test_math_utils.py that imports the function and tests add(2, 3). Run the test and write the result (PASS/FAIL) into test_result.txt."
    memory.add_interaction("user", f"Goal: {goal}")
    print(f"Goal Inputted: {goal}")
    
    while True:
        try:
            tasks = qwen.generate_task(memory)
        except Exception as e:
            print("Error fetching Qwen output:", e)
            time.sleep(3)
            continue
            
        if not tasks:
            print("⚠️ No tasks — skipping")
            continue
            
        memory.add_interaction("assistant", json.dumps(tasks))
            
        execution_log = []
        for t in tasks:
            # Re-normalize if not fully processed
            if "type" not in t:
                task = normalize_task(t)
            else:
                task = t
                
            print("EXECUTING:", task)
            result = executor.run(task)
            execution_log.append({"task": task, "result": result})

        # --- ChatGPT GOVERNANCE ---
        memory.add_interaction("system", f"Execution Results: {json.dumps(execution_log)}")
        
        context = {
            "goal": "math test execution",
            "execution_log": execution_log,
            "files_created": [],
            "expected_result": "PASS"
        }
        for f in ["math_utils.py", "test_math_utils.py", "test_result.txt"]:
            if os.path.exists(os.path.join(workspace.base_dir, f)):
                context["files_created"].append(f)
        
        decision_obj = call_chatgpt(context)
        decision = decision_obj.get("decision")
        print("ChatGPT decision:", decision)
        
        if decision == "CONTINUE":
            memory.add_interaction("user", "Execution successful. Output recorded. Continue execution to fulfill the goal.")
            continue
            
        elif decision == "FIX":
            fix_task = decision_obj.get("next_task")
            
            # FORCE JSON PARSING RETRY
            if not isinstance(fix_task, dict):
                print("❌ Invalid ChatGPT response — retry once")
                decision_obj = call_chatgpt(context)
                fix_task = decision_obj.get("next_task")
                if not isinstance(fix_task, dict):
                    print("❌ Invalid ChatGPT response — STOP")
                    sys.exit(1)
            
            if not fix_task:
                print("❌ FIX requested but no next_task — STOP")
                sys.exit(1)
                
            print("EXECUTING FIX:", fix_task)
            executor.run(fix_task)
                
            continue
            
        elif decision == "COMPLETE":
            print("✅ MINI DEV + TEST AGENT COMPLETE")
            sys.exit(0)
            
        else:
            print("❌ Unknown decision — STOP")
            sys.exit(1)

if __name__ == "__main__":
    start_daemons()
    if not is_qwen_running():
        start_qwen_server()
        
    run_autonomous_loop()
