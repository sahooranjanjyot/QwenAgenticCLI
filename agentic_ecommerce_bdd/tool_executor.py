import os
import subprocess
import time

running_processes = {}

def get_active_pids():
    global running_processes
    active = []
    for pid, proc in list(running_processes.items()):
        if proc.poll() is None:
            active.append(pid)
        else:
            del running_processes[pid]
    return active

def extract_content(content):
    # 🔥 HANDLE BOTH STRING + DICT
    if isinstance(content, dict):
        return content.get("payload", "")
    return content or ""

def execute_action(action, caller=None):
    print(f"⚙️ EXECUTOR CALLED BY: {caller}")
    print(f"📦 ACTION: {action}")

    if not isinstance(action, dict):
        return "❌ Invalid action format"

    action_type = action.get("action_type") or action.get("action")

    if action_type == "COMPLETE":
        return "COMPLETE"

    # ===============================
    # READ FILE
    # ===============================
    if action_type == "READ_FILE":
        target = action.get("target")

        if not target or not os.path.exists(target):
            return "FILE NOT FOUND"

        with open(target, "r") as f:
            content = f.read()
            
        return content

    # ===============================
    # WRITE / FIX FILE
    # ===============================
    if action_type in ["WRITE_FILE", "FIX"]:
        target = action.get("target")
        raw_content = action.get("content")

        content = extract_content(raw_content)

        if not target or not content:
            return "INVALID WRITE"

        # 🔥 SAFE STRING CHECK
        if os.path.exists(target):
            with open(target, "r") as f:
                existing = f.read()

            if existing.strip() == content.strip():
                print("🚫 BLOCKED: SAME CONTENT")
                return "NO_CHANGE"

            print("⚠️ OVERWRITING EXISTING FILE")

        with open(target, "w") as f:
            f.write(content)

        return f"WROTE {target}"

    # ===============================
    # RUN COMMAND
    # ===============================
    if action_type == "RUN_COMMAND":
        cmd = action.get("command")
        if not cmd:
            return "EMPTY COMMAND"

        if cmd.strip().endswith("&"):
            print(f"🔄 LAUNCHING BACKGROUND PROCESS: {cmd}")
            log_file = open("server.log", "a")
            proc = subprocess.Popen(cmd, shell=True, stdout=log_file, stderr=subprocess.STDOUT)
            running_processes[proc.pid] = proc
            time.sleep(2) # Give the server a moment to start
            return f"STARTED BACKGROUND COMMAND: {cmd} with PID {proc.pid}"

        return subprocess.getoutput(cmd)

    return "UNKNOWN ACTION"

# ============================================================
# CLASS-BASED EXECUTOR (BACKWARD COMPATIBILITY)
# ============================================================
class ToolExecutor:
    def execute(self, action, caller="ToolExecutor"):
        return execute_action(action, caller=caller)
