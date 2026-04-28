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

    if all(not action.get(k) for k in ["content", "command", "target"]):
        return {"decision": "FAIL", "reason": "Completely empty action", "feedback": "Completely empty action"}

    print("✅ GOVERNANCE PASS")
    return {"decision": "PASS", "feedback": "Looks good."}
