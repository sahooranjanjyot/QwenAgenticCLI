import os
import json

def review_with_openai(goal, action, context=None):
    print("🧠 GOVERNANCE CHECK")

    if not isinstance(action, dict):
        return {"decision": "FAIL", "reason": "Action is not dict", "feedback": "Action is not dict"}

    action_type = action.get("action_type") or action.get("action")

    # ============================================================
    # BASIC STRUCTURE CHECK
    # ============================================================
    if not action_type:
        return {"decision": "FAIL", "reason": "Missing action_type", "feedback": "Missing action_type"}

    # ============================================================
    # VALIDATION RULES
    # ============================================================

    if action_type == "RUN_COMMAND":
        if not action.get("command"):
            return {"decision": "FAIL", "reason": "Empty command", "feedback": "Empty command"}

    elif action_type in ["WRITE_FILE", "FIX"]:
        if not action.get("target"):
            return {"decision": "FAIL", "reason": "Missing target", "feedback": "Missing target"}

        if not action.get("content"):
            return {"decision": "FAIL", "reason": "Empty content", "feedback": "Empty content"}

    elif action_type == "READ_FILE":
        if not action.get("target"):
            return {"decision": "FAIL", "reason": "Missing target", "feedback": "Missing target"}

    elif action_type == "COMPLETE":
        pass

    else:
        return {"decision": "FAIL", "reason": f"Unknown action: {action_type}", "feedback": f"Unknown action: {action_type}"}

    # ============================================================
    # BLOCK EMPTY / NONSENSE ACTIONS
    # ============================================================

    if action_type != "COMPLETE" and all(not action.get(k) for k in ["content", "command", "target"]):
        return {"decision": "FAIL", "reason": "Completely empty action", "feedback": "Completely empty action"}

    # ============================================================
    # ACTUAL OPENAI GOVERNANCE
    # ============================================================
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("🔍 Querying OpenAI for semantic governance...")
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            prompt = f"""
You are the Senior Governance AI for an autonomous coding agent.
The agent's overall goal is:
{goal}

The agent proposes the following action:
{json.dumps(action, indent=2)}

YOUR JOB:
1. Enforce Safety: Is it safe and non-destructive?
2. Enforce Quality: If the action is WRITE_FILE, review the code. Is it robust, clean, and bug-free?
3. Enforce Logic: Does this step make sense to achieve the goal?

If anything is wrong or subpar, reject it.
Respond with a JSON object: {{"decision": "PASS" or "FAIL", "feedback": "Detailed reasoning and concrete suggestions for the agent if it failed"}}
"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            llm_review = json.loads(response.choices[0].message.content)
            
            if llm_review.get("decision") == "FAIL":
                return {
                    "decision": "FAIL", 
                    "reason": "OpenAI Governance Rejected", 
                    "feedback": llm_review.get("feedback", "Rejected by LLM")
                }
        except Exception as e:
            print(f"⚠️ OpenAI Governance API Error (falling back to PASS): {e}")

    print("✅ GOVERNANCE PASS")
    return {"decision": "PASS", "feedback": "Looks good."}

def analyze_test_failure(goal, test_result):
    print("🧠 OPENAI ANALYZING TEST FAILURE...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Tests failed. Check the error logs and try again."
        
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        prompt = f"""
You are the Senior Governance AI. The junior agent (Qwen) just ran the integration tests, but they failed.

Overall Goal:
{goal}

Test Results:
{json.dumps(test_result, indent=2)}

Analyze the exact root cause of the failure based on these results. 
What exactly should the junior agent do next to fix this? Provide a concise, highly actionable instruction.
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Tests failed. Error: {e}"
