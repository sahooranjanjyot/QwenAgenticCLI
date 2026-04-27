import os
import sys
import json
import time

from qwen_agent import QwenAgent
from tool_executor import ToolExecutor
from agent_memory import AgentMemory
import safety_policy
from completion_validator import chatgpt_validate

def run():
    print("\nStarting Main Loop: QWEN AUTONOMOUS AGENT ACTIVE")
    qwen = QwenAgent()
    executor = ToolExecutor("workspace")
    memory = AgentMemory()
    
    goal = "Create math_utils.py with add(a,b), create test_math_utils.py against it, run the test, write PASS/FAIL to test_result.txt, then propose COMPLETE."
    print("Goal:", goal)
    
    last_observation = None
    loop_count = 0
    max_loops = 30
    
    while loop_count < max_loops:
        loop_count += 1
        print(f"\n--- LOOP {loop_count} ---")
        
        # 1. Qwen decides
        action = qwen.next_action(goal, memory, last_observation)
        
        if not action or "action_type" not in action:
            print("❌ Invalid action returned by Qwen:", action)
            last_observation = {"status": "ERROR", "message": "You must return a valid JSON action_type."}
            continue
            
        print(f"QWEN ACTION: [{action.get('action_type')}] Target: {action.get('target')} Reason: {action.get('thought')}")
        
        # 2. Safety filter
        if safety_policy.rejects(action):
            print("🛑 STOPPING SYSTEM DUE TO SAFETY")
            sys.exit(1)
            
        # Record what Qwen decided
        memory.add("assistant", json.dumps(action))
            
        # 3. Check for COMPLETE
        if action["action_type"] == "COMPLETE":
            print("Qwen proposed COMPLETE. Triggering ChatGPT Audit...")
            validation = chatgpt_validate(goal, memory)
            print("ChatGPT Audit:", validation)
            if validation.get("decision") == "COMPLETE":
                print("✅ WEB APP AGENT TEST PASSED")
                sys.exit(0)
            else:
                reason = validation.get("reason", "Incomplete criteria")
                print(f"❌ ChatGPT REJECTED COMPLETION: {reason}")
                last_observation = {
                    "status": "REJECTED_BY_CHATGPT",
                    "reason": reason,
                    "instruction": "Fix the rejection reason and propose COMPLETE again."
                }
                memory.add("system", f"Audit Rejected: {reason}")
                continue
                
        # 4. Tool Execution
        print("EXECUTING TOOL...")
        observation = executor.execute(action)
        print("OBSERVATION:", str(observation)[:500])
        
        # Record observation
        memory.add("user", f"Execution Observation:\n{json.dumps(observation)}")
        last_observation = observation
        
        time.sleep(1) # Prevent hot looping if bugged

    print("❌ Max loops reached.")
    sys.exit(1)

if __name__ == "__main__":
    run()
