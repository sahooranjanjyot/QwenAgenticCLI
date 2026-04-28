import subprocess

def normalize_command(cmd: str) -> str:
    if not isinstance(cmd, str): return cmd
    cmd = cmd.replace("/users/", "/users")
    cmd = cmd.replace("/health/", "/health")
    cmd = cmd.replace("localhost", "127.0.0.1")
    if "8002" not in cmd and "127.0.0.1" in cmd:
        cmd = cmd.replace("127.0.0.1", "127.0.0.1:8002")
    return cmd

def execute_and_decide(action, state):
    if "command" in action:
        action["command"] = normalize_command(action["command"])
        
    cmd = action.get("command")

    if not cmd:
        return None, state, False

    print(f"▶️ EXEC: {cmd}")

    result = subprocess.getoutput(cmd)
    print(f"📥 OUTPUT: {result}")

    # SIMPLE LOGIC
    if "/health" in cmd:
        if "ok" in result:
            print("✅ SYSTEM HEALTHY")
            return None, state, True

    return None, state, False
