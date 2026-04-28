import subprocess
import json

def run(cmd):
    return subprocess.getoutput(cmd)

def run_tests():
    results = {
        "health": False,
        "create_user": False,
        "get_users": False,
        "all_pass": False,
        "details": {}
    }

    try:
        # 1. HEALTH CHECK
        health = run("curl -sS http://127.0.0.1:8002/health")
        results["details"]["health"] = health

        if "ok" in health:
            results["health"] = True

        # 2. CREATE USER
        create = run("""curl -sS -X POST http://127.0.0.1:8002/users \
-H "Content-Type: application/json" \
-d '{"name":"TestUser"}'""")

        results["details"]["create_user"] = create

        if "id" in create or "exists" in create:
            results["create_user"] = True

        # 3. GET USERS
        users = run("curl -sS http://127.0.0.1:8002/users")
        results["details"]["get_users"] = users

        if "[" in users:
            results["get_users"] = True

        # FINAL RESULT
        if results["health"] and results["create_user"] and results["get_users"]:
            results["all_pass"] = True

    except Exception as e:
        results["details"]["error"] = str(e)

    return results
