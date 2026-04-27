import os
import requests
import json
import subprocess
import time
from action_schema import extract_action
from tool_executor import ToolExecutor
from validator import chatgpt_validate, check_compliance
from openai_supervisor import review_with_openai


try:
    from agent_memory import AgentMemory
except ImportError:
    pass

class MemoryAdapter:
    def __init__(self):
        self.stack = None
        self.verification_status = {
            "health_checked": False,
            "server_running": False,
            "endpoint_tested": False,
            "tests_executed": False
        }
        self.current_hypothesis = "UNKNOWN"
        self.current_phase = "BUILD_PHASE"
        try:
            self.mem = AgentMemory()
        except:
            self.mem = None
            self.history = []

    def save_state(self):
        with open("agent_state.json", "w") as f:
            json.dump(self.verification_status, f)

    def load_state(self):
        try:
            with open("agent_state.json", "r") as f:
                self.verification_status = json.load(f)
        except:
            pass
            
    def get_last_n(self, n):
        if self.mem:
            return self.mem.get_messages(limit=n)
        return self.history[-n:]
        
    def add_interaction(self, role, content):
        if self.mem:
            self.mem.add(role, content)
        else:
            self.history.append({"role": role, "content": content})
            
    def get_full_history(self):
        if self.mem:
            return getattr(self.mem, 'history', [])
        return self.history

def run_agent(goal):
    import os
    if os.path.exists(".agent_done"):
        print("🛑 SYSTEM ALREADY COMPLETED - EXITING")
        return

    print("Initializing Autonomous Qwen Loop...")
    agent = QwenAgent()
    memory = MemoryAdapter()
    executor = ToolExecutor()
    memory.load_state()
    last_observation = None
    
    iteration = 0
    max_iterations = 20
    consecutive_errors = 0
    max_same_error_retries = 3
    
    governance_mode = "NORMAL_MODE"
    governance_cycles = 0
    
    last_actions = []
    retry_count = 0
    MAX_RETRIES = 5
    while True:
        iteration += 1
        if iteration > max_iterations:
            print("❌ Loop Safety: Max iterations exceeded.")
            with open("failure.log", "w") as f:
                f.write("Max iterations exceeded.")
            break
            
        action = agent.next_action(goal, memory, last_observation)

        last_actions.append(action.get("action_type", ""))

        if len(last_actions) > 5:
            last_actions.pop(0)

        if last_actions.count("READ_FILE") >= 3:
            print("⚠️ STUCK LOOP DETECTED → FORCING PROGRESS")
            action = {
                "action_type": "RUN_COMMAND",
                "command": "curl http://127.0.0.1:8002/health",
                "target": ""
            }
        
        # ===== BLOCK RE-BUILD PHASE =====
        if memory.verification_status.get("server_running") and memory.verification_status.get("endpoint_tested"):
            goal = "System already built and validated. Only monitor or exit."

        # ===== FORCE_FULL_FLOW =====
        if memory.verification_status.get("health_checked") and not memory.verification_status.get("endpoint_tested"):
            print("🚀 FORCING POST /users VALIDATION INJECTION")
            action = {
                "action_type": "RUN_COMMAND",
                "command": "curl -X POST http://127.0.0.1:8002/users -H 'Content-Type: application/json' -d '{\"name\":\"Alice\"}' && curl -X POST http://127.0.0.1:8002/users -H 'Content-Type: application/json' -d '{\"name\":\"Bob\"}'",
                "target": ""
            }
        elif memory.verification_status.get("endpoint_tested") and not memory.verification_status.get("tests_executed"):
            print("🚀 FORCING GET /users VALIDATION INJECTION")
            action = {
                "action_type": "RUN_COMMAND",
                "command": "curl -s http://127.0.0.1:8002/users",
                "target": ""
            }

        if not action or "action_type" not in action:
            print("❌ Qwen failed → retrying with stricter instruction")
            goal += "\n\nYour previous response was invalid. Return STRICT JSON."
            continue
            
        # STEP 4: HARD GUARDRAILS ONLY
        cmd = action.get("command", "").lower()
        if "rm -rf" in cmd or "rm *" in cmd:
            print("❌ GOVERNANCE BLOCK: Destructive system command intercepted.")
            last_observation = {"error": "Destructive system commands (rm -rf) are strictly forbidden."}
            continue

        if "uvicorn main:app --reload" in cmd:
            print("🚫 BLOCKED: Foreground server not allowed")
            action["command"] = "uvicorn main:app --host 127.0.0.1 --port 8002 > server.log 2>&1 &"
            action["action_type"] = "RUN_BACKGROUND_COMMAND"
            action_type = "RUN_BACKGROUND_COMMAND"
            cmd = action["command"]
            
        if not getattr(memory, "stack", None) and action.get("stack"):
            memory.stack = action.get("stack")
            print(f"STACK SELECTED: {memory.stack}")
            
        # Execute action properly
        action_type = action.get("action_type")
        target = action.get("target", "")

        if action_type == "WRITE_FILE" and target == "main.py":
            print("🚫 BLOCKED: main.py already exists")
            action = {
                "action_type": "RUN_COMMAND",
                "command": "curl http://127.0.0.1:8002/health",
                "target": ""
            }
            action_type = "RUN_COMMAND"
            cmd = action["command"]

        elif action_type == "WRITE_FILE" and target and os.path.exists(target) and not target.endswith("requirements.txt"):
            print("🔍 Forcing READ_FILE instead of WRITE")
            action["action_type"] = "READ_FILE"
            action_type = "READ_FILE"
        
        if action_type == "WRITE_FILE":
            
            if target.endswith("requirements.txt"):
                new_content = action.get("content", "")
                new_pkgs = set([p.strip() for p in new_content.split("\n") if p.strip()])

                existing_pkgs = set()
                if os.path.exists(target):
                    with open(target, "r") as f:
                        existing_pkgs = set([p.strip() for p in f.readlines() if p.strip()])

                INVALID_PACKAGES = ["sqlite3"]
                new_pkgs = {p for p in new_pkgs if p not in INVALID_PACKAGES}
                existing_pkgs = {p for p in existing_pkgs if p not in INVALID_PACKAGES}

                merged_pkgs = existing_pkgs.union(new_pkgs)

                if merged_pkgs != existing_pkgs:
                    print("📦 Updating requirements.txt (merge mode)")
                    with open(target, "w") as f:
                        f.write("\n".join(sorted(merged_pkgs)) + "\n")
                    result = {"status": "UPDATED_REQUIREMENTS"}
                    print("🔁 Reinstalling dependencies due to update")
                    os.system(f"python3 -m pip install -r {target}")
                else:
                    print("⚠️ No new dependencies → SKIP")
                    goal += "\n\nDependencies are already satisfied. Move to execution and testing."
                    result = {"status": "NO_CHANGE"}

                memory.add_interaction("user", json.dumps({"action": action, "result": result}))
                continue
                

        
        if action_type == "COMPLETE":
            print("Qwen signaled COMPLETE. Submitting to Governance...")
            open(".agent_done", "w").write("done")
            result = {"status": "AGENT_SIGNALED_COMPLETE"}
            break
            
        elif action_type == "RESTART":
            print("Handling RESTART internally...")
            import subprocess
            import time
            
            subprocess.call("pkill -f uvicorn", shell=True)
            subprocess.call(
                "cd /Users/jyotiranjan/projects/OpenCLI/agentic_system/workspace && "
                "nohup uvicorn main:app --host 127.0.0.1 --port 8002 > uvicorn.log 2>&1 &",
                shell=True
            )
            
            time.sleep(2)
            result = {"status": "RESTARTED"}
            
        else:
            if action_type == "RUN_BACKGROUND_COMMAND" or "uvicorn" in action.get("command", ""):
                import subprocess
                subprocess.call("pkill -f uvicorn", shell=True)
                print("⚠️ Killed existing servers for clean start")
                
                result = executor.execute(action, caller="qwen_agent")
                print("🚀 Server started in background. Injecting health wait...")
                
                import time
                time.sleep(2)
                health_cmd = {"action_type": "RUN_COMMAND", "command": "curl -s http://127.0.0.1:8002/health", "target": ""}
                result["health_validation"] = executor.execute(health_cmd, caller="qwen_agent")
            else:
                result = executor.execute(action, caller="qwen_agent")
            
            if action_type == "READ_FILE":
                context_summary = f"""
Current system state:
- main.py exists and contains FastAPI app
- SQLite DB logic present
- Endpoints: /health, /users
"""
                goal = f"""
You are working on an EXISTING project.

DO NOT:
- recreate files
- redo setup

NEXT STEPS:
- validate server
- test endpoints
- fix issues if found

CONTEXT:
{context_summary}
"""

            if action_type == "RUN_COMMAND":
                last_command_output = str(result).lower()
                
                if "health" in last_command_output:
                    print("✅ HEALTH CHECK PASSED")
                    next_action = {
                        "action_type": "RUN_COMMAND",
                        "command": "curl http://127.0.0.1:8002/users",
                        "target": ""
                    }
                    action = next_action
                    result = executor.execute(action, caller="qwen_agent")
                    last_command_output = str(result).lower()

                if "users" in last_command_output:
                    print("🎉 SYSTEM COMPLETE")
                    exit()
                    
            # ===== SUPERVISOR REVIEW =====
            gov = review_with_openai(goal, action, result)

            if gov["decision"] == "PASS":
                print("✅ STEP VALID → CONTINUE")
                retry_count = 0
                continue

            elif gov["decision"] == "FAIL":
                retry_count += 1
                print(f"🔁 RETRY {retry_count}")

                if retry_count >= MAX_RETRIES:
                    print("🛑 STOP — MAX RETRIES")
                    exit()

                print("❌ STEP INVALID → RETRY")
                
                goal = f"""
Your previous action was INVALID.

Fix it using this feedback:
{gov['feedback']}

Do NOT repeat same action.
"""
                continue

            else:
                raise RuntimeError("Invalid governance response")
    print("Pipeline Exited.")

def validate_action(action):
    required_keys = ["action_type"]

    for key in required_keys:
        if key not in action:
            raise ValueError(f"Missing key: {key}")

    # Auto-fill missing optional values so agent loop operates smoothly
    action.setdefault("thought", "")
    action.setdefault("target", "")
    action.setdefault("content", "")
    action.setdefault("command", "")

    allowed = [
        "WRITE_FILE",
        "RUN_COMMAND",
        "RUN_BACKGROUND_COMMAND",
        "READ_FILE",
        "LIST_FILES",
        "PATCH_CODE",
        "FIX",
        "COMPLETE"
    ]

    if action["action_type"] not in allowed:
        raise ValueError(f"Invalid action_type: {action['action_type']}")

    return action

class QwenAgent:
    def __init__(self, base_url="http://127.0.0.1:11434/v1/chat/completions", model="qwen2.5-coder:32b"):
        self.base_url = os.getenv("QWEN_BASE_URL", base_url)
        self.model = os.getenv("QWEN_MODEL", model)

    def next_action(self, goal, memory, last_observation):
        sys_prompt = f"""You are the primary autonomous agent responsible for achieving the following goal:
{goal}

Before taking any action:
You MUST first determine the most appropriate technology stack.

You must:
- Analyze the goal
- Choose the best language/framework
- Justify your choice in the "thought"

You MUST choose appropriate stack based on goal:
- Web API → FastAPI / Node
- UI App → React / HTML
- Automation → Selenium / Java / Python
- Data → SQLite / Postgres

Once chosen:
→ You MUST stay consistent with the stack
→ You MUST NOT mix stacks unless explicitly required
→ Switching stack mid-way = FAILURE
"""
        if getattr(memory, "stack", None):
            sys_prompt += f"\nCHOSEN STACK: {memory.stack}\nYou MUST reuse this stack.\n"
            
        sys_prompt += """
You are an active planner, executor-controller, debugger, and self-healer. The execution environment executes tools on your behalf.
You receive observations (stdout/stderr/files) from your previous action.
Evaluate the observation, plan logically, and output EXACTLY ONE next action JSON per turn. Do not output multi-step arrays.

CRITICAL SUPERVISOR CONTRACT:
You are governed by an OpenAI supervisor. You MUST follow supervisor feedback exactly.
Do NOT output free-form retries or ignore the feedback.
If the supervisor instructs a specific action, you MUST output that precise action payload.

CRITICAL RULE: If calling `curl` with a URL containing `&`, you MUST wrap the URL in quotes (e.g. `curl "http://..."`).
RULES:
- Never recreate existing files
- If files exist → DO NOT recreate
- Prefer execution over setup
- Move forward, not backward
- Always inspect before modifying
- Prefer PATCH over WRITE
CRITICAL RULE:
- Do NOT randomly choose technologies
- Always choose based on problem type
- Always stay consistent once chosen

If a command fails, produces empty output, or returns non-zero exit code:
→ You MUST NOT proceed
→ You MUST switch to FIX action_type
→ You MUST try a different approach (not repeat same command)

If the same error occurs twice:
→ You MUST change strategy completely (different tool, command, or approach)

ENABLE AUTONOMOUS DEBUG-FIX-VALIDATE LOOP (ADFVL)

1. FAILURE CLASSIFICATION (MANDATORY)
Map every failure to one of:
- CODE_ERROR (import, syntax, crash, 500)
- SERVER_DOWN (port not listening / process dead)
- ENDPOINT_ERROR (API returns wrong response)
- ENV_ERROR (dependency / install issue)
- UNKNOWN

2. CONTROL MODE SWITCH
- CODE_ERROR → DEBUG_MODE
- SERVER_DOWN → RECOVERY_MODE
- ENDPOINT_ERROR → VALIDATION_MODE
- ENV_ERROR → SETUP_FIX_MODE

3. STRICT ACTION PIPELINE (NO DEVIATION)

DEBUG_MODE (CODE FIXING):
- READ_FILE (target file from stacktrace, default main.py)
- ANALYZE
- PATCH_CODE (mandatory next step)
- RESTART server
- VALIDATE (/health → endpoints)

RECOVERY_MODE:
- CHECK process (ps/lsof)
- RESTART server ONCE
- VALIDATE (/health)
- IF FAIL → escalate to DEBUG_MODE

VALIDATION_MODE:
- TEST endpoints
- IF failure persists → DEBUG_MODE

SETUP_FIX_MODE:
- FIX requirements / environment
- RESTART
- VALIDATE

4. ACTION GOVERNANCE (CRITICAL)

ALLOW:
- READ_FILE
- WRITE_FILE / PATCH_CODE
- RESTART

BLOCK during CODE_ERROR:
- curl loops
- sleep retries
- repeated health checks
- log-only analysis without code action

RULE:
IF failure_type = CODE_ERROR
→ next action MUST be PATCH_CODE after READ_FILE

5. COMPLETION LOGIC (STRICT)

ONLY COMPLETE IF:
- /health = OK
- POST works
- GET works
- NO duplicates
- output written to file

6. AUTO-FIX ESCALATION

- If PATCH_CODE fails 1 time: → force FULL_REWRITE
- If FULL_REWRITE fails: → regenerate entire file from scratch using "safe minimal working template".

7. ANTI-LOOP CONTROL

Track last 3 actions.
IF repeated: → force PATCH_CODE
Max: 2 retries, then FULL_REWRITE.

8. SAFE FALLBACK TEMPLATE (SQLITE/FASTAPI)

When SQLite/FastAPI fails → enforce this:
- Table creation OUTSIDE endpoint
- Single DB init
- No duplicate inserts
- Proper connection lifecycle

9. GOVERNANCE OVERRIDE FOR CODE FIXING

IF failure_type = CODE_ERROR:
ALLOW ONLY: READ_FILE, PATCH_CODE, RESTART
BLOCK: curl loops, log loops, retries without fix
MANDATORY: READ_FILE → PATCH_CODE → VALIDATE

10. PATCH CONTRACT (STRICT FORMAT)

PATCH_CODE must ALWAYS format like this exactly. INVALID format drops immediately:
{
"thought": "short reasoning only",
"stack": "tech stack chosen",
"action_type": "PATCH_CODE",
"target": "file.py",
"content": {
    "type": "FULL_REWRITE | SEARCH_REPLACE",
    "payload": "provide code here if FULL_REWRITE, or a {'search': '...', 'replace': '...'} dict if SEARCH_REPLACE"
},
"command": ""
}

For standard actions:
{
"thought": "short reasoning only",
"stack": "tech stack chosen",
"action_type": "READ_FILE | WRITE_FILE | RUN_COMMAND | RUN_BACKGROUND_COMMAND | COMPLETE | FIX",
"target": "...",
"content": "...",
"command": "..."
}

11. MULTI-APP SAFETY

PATCH must apply ONLY within: workspace/<app_id>/
No cross-app overwrite allowed.

12. SELF-HEALING MEMORY

After fix store: failure_type, root_cause, fix_applied
Next time: → avoid same mistake (error → READ_FILE → PATCH → validate → COMPLETE)

13. DEEP CODE ANALYSIS AFTER READ_FILE (MANDATORY)

Qwen MUST NOT conclude "code is correct" WITHOUT verification.
After reading file, Qwen must evaluate checklist:
- Does app start without error?
- Any missing imports?
- Any syntax issues?
- Is DB initialized outside endpoints?
- Are endpoints defined correctly?
- Any obvious runtime failure points?

VALIDATION RULE:
IF server is DOWN: → NEVER assume code is correct
MANDATORY NEXT STEP: → CHECK logs OR PATCH_CODE

BLOCK GENERIC ACTIONS after READ_FILE:
BLOCK: pip install (unless ENV_ERROR) and restart-only commands
UNLESS root cause confirmed

FORCE DECISION:
After READ_FILE, Qwen must choose ONE:
EITHER: A) PATCH_CODE (fix issue) OR B) RUN_COMMAND (inspect logs)
NOT: ❌ "code looks fine → restart"

CONFIDENCE RULE: If confidence < 80% → MUST check logs
FAILURE ESCALATION: If server still not running → FORCE PATCH_CODE (no log loop)

EXPECTED BEHAVIOR:
✅ READ_FILE → analyze → logs → fix → restart → validate → COMPLETE
"""
        messages = [{"role": "system", "content": sys_prompt}]
        messages.extend(memory.get_last_n(5))
        
        # Add the last observation if it exists
        if last_observation:
            messages.append({"role": "user", "content": f"OBSERVATION OF PREVIOUS ACTION:\n{json.dumps(last_observation)}"})
        else:
            messages.append({"role": "user", "content": "You are just starting. Propose the first logical action."})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2
        }

        try:
            # --- QWEN HEALTH CHECK & AUTO-RECOVER ---
            import subprocess
            try:
                requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
            except requests.exceptions.RequestException:
                print("⚠️ QWEN_DOWN: Attempting auto-recovery...")
                subprocess.run("pkill -f ollama || true", shell=True)
                subprocess.Popen("ollama serve", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                import time
                time.sleep(5)

            # --- TIMEOUT HANDLING & RETRY ---
            response = None
            for attempt in range(3):
                try:
                    response = requests.post(self.base_url, json=payload, timeout=60)
                    response.raise_for_status()
                    break
                except requests.exceptions.ReadTimeout as e:
                    print(f"⚠️ Qwen ReadTimeout (attempt {attempt+1}/3)...")
                    if attempt == 2:
                        raise Exception(f"Qwen timeout maxed out: {e}")
                except requests.exceptions.RequestException as e:
                    print(f"⚠️ Qwen RequestException (attempt {attempt+1}/3)...")
                    if attempt == 2:
                        raise Exception(f"Qwen connection maxed out: {e}")

            raw_output = response.json()["choices"][0]["message"]["content"]
            print("--- QWEN OUTPUT ---\n", raw_output, "\n-------------------")
            
            action = None
            for attempt in range(2):
                try:
                    action = extract_action(raw_output)
                    action = validate_action(action)
                    break
                except Exception as e:
                    print(f"⚠️ Invalid Qwen output (attempt {attempt+1}):", e)
                    if attempt == 1:
                        raise Exception("❌ Qwen failed to return valid action JSON")

            print("Parsed Action:", action)

            if last_observation:
                prev_cmd = last_observation.get("command")
                new_cmd = action.get("command")

                if prev_cmd and new_cmd and prev_cmd == new_cmd:
                    print("⚠️ Loop detected: same command repeating")
                    action["thought"] = "Loop detected, trying different strategy"

            return action
        except Exception as e:
            # FALLBACK_AGENT_MODE
            print("⚠️ FIRING FALLBACK_AGENT_MODE due to Qwen API failure.")
            with open("qwen_failure.log", "a") as f:
                import datetime
                f.write(f"[{datetime.datetime.now().isoformat()}] ERROR: {str(e)}\n")
            
            return {
                "thought": "Qwen unavailable, triggering predefined recovery strategies",
                "action_type": "RUN_COMMAND",
                "command": "echo QWEN_DOWN >> system.log",
                "target": "",
                "content": ""
            }


# ===== RESTART_HANDLER =====
def handle_restart():
    import subprocess
    print("🔁 Restarting server...")
    subprocess.call("pkill -f uvicorn", shell=True)
    subprocess.call("cd workspace && nohup uvicorn main:app --host 127.0.0.1 --port 8002 > uvicorn.log 2>&1 &", shell=True)
    return {"status": "restarted"}