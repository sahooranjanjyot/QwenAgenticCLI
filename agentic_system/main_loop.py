import time
from qwen_agent import QwenAgent
from tool_executor import execute_action
from openai_supervisor import review_with_openai, analyze_test_failure
from agent_memory import AgentMemory
from test_engine import run_tests

memory = AgentMemory()

def read_goal():
    with open("goal.txt", "r") as f:
        return f.read().strip()

goal = read_goal()
print(f"🎯 GOAL: {goal}")

retries = 0
MAX_RETRIES = 15
last_observation = None

while True:

    # =========================
    # STEP 1 — QWEN DECISION
    # =========================
    agent_goal = goal
    import os
    workspace_files = [f for f in os.listdir('.') if os.path.isfile(f) and not f.endswith('.log') and f not in ["goal.txt", "users.db"]]
    agent_goal += f"\n\nCURRENT FILES IN WORKSPACE: {workspace_files}\nCheck if you need to run any commands (e.g., uvicorn) to start the server."
    if memory.get_all():
        agent_goal += "\n\nMEMORY/FEEDBACK:\n" + str(memory.get_all()[-5:])
    agent_goal = agent_goal + "\nRULE: Always READ_FILE before WRITE_FILE. Do not rewrite same file repeatedly."
    try:
        action = QwenAgent().next_action(agent_goal, memory.get_all(), last_observation)
        print(f"\n🧠 QWEN ACTION:\n{action}")
    except Exception as e:
        print(f"❌ QWEN PARSE ERROR: {e}")
        memory.add("system", {"type": "parse_error", "error": str(e), "instruction": "Return exactly ONE valid JSON object, not a list. Ensure you escape all newlines and quotes inside strings properly."})
        last_observation = {"error": f"Failed to parse action: {e}. Return ONE valid JSON object (not an array) with properly escaped strings."}
        retries += 1
        continue

    # =========================
    # STEP 2 — GOVERNANCE
    # =========================
    governance = review_with_openai(goal, action, memory.get_all())
    print(f"🛡️ GOVERNANCE:\n{governance}")

    if governance.get("decision") == "FAIL":
        print("❌ BLOCKED BY GOVERNANCE")

        memory.add("system", {
            "type": "governance_feedback",
            "data": governance,
            "instruction_to_qwen": "Your previous action was rejected. Return ONLY valid JSON with a useful action. If action_type is WRITE_FILE or FIX, target and content must be non-empty. If action_type is RUN_COMMAND, command must be non-empty. If action_type is READ_FILE, target must be non-empty."
        })

        retries += 1
        continue

    print("✅ APPROVED")

    # =========================
    # STEP 3 — EXECUTION
    # =========================
    print("🚀 EXECUTING ACTION (NO BLOCKS)")
    result = execute_action(action, caller="qwen_agent")
    print(f"⚙️ RESULT:\n{result}")
    last_observation = {"action_result": result}

    # =========================
    # STEP 4 — TEST ENGINE
    # =========================
    test_result = run_tests()
    print(f"🧪 TEST RESULT:\n{test_result}")

    if not test_result.get("all_pass"):
        print("❌ TEST FAILED → FEEDBACK TO QWEN")

        if result == "COMPLETE":
            last_observation = {"error": "You returned COMPLETE, but tests failed. Do NOT return COMPLETE until tests pass. Check if you need to start the server."}
            print("🚫 REJECTED COMPLETE: Tests are failing.")

        openai_suggestion = analyze_test_failure(goal, test_result)
        print(f"💡 OPENAI SUGGESTION:\n{openai_suggestion}")

        memory.add("system", {
            "type": "test_failure_with_guidance",
            "test_result": test_result,
            "senior_developer_guidance": openai_suggestion
        })

    else:
        print("✅ ALL TESTS PASSED")
        import os
        if not os.path.exists("app_test_result.txt"):
            last_observation = {
                "success": "All tests passed perfectly! However, you MUST satisfy step 9 of the goal: write the test results to 'app_test_result.txt' with 'PASS' inside. Use WRITE_FILE to create app_test_result.txt before outputting COMPLETE.",
                "test_output_for_file": test_result
            }
        else:
            last_observation = {"success": "All tests passed perfectly, and app_test_result.txt exists! The goal is completely achieved. You MUST now output action_type: 'COMPLETE' to finish."}

    # =========================
    # STEP 5 — SUCCESS CHECK
    # =========================
    import os
    if result == "COMPLETE" and test_result.get("all_pass") and os.path.exists("app_test_result.txt"):
        print("🎉 GOAL ACHIEVED")
        break
    elif result == "COMPLETE" and test_result.get("all_pass"):
        last_observation = {"error": "You returned COMPLETE, but app_test_result.txt does not exist. Read step 9 in the goal. You must WRITE_FILE app_test_result.txt with the test results."}
        print("🚫 REJECTED COMPLETE: Missing app_test_result.txt.")

    retries += 1

    if retries >= MAX_RETRIES:
        print("🛑 MAX RETRIES — EXIT")
        break

    time.sleep(1)
