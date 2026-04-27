import os
import subprocess

class ToolExecutor:
    def __init__(self, workspace_dir="workspace"):
        self.workspace = os.path.abspath(workspace_dir)
        os.makedirs(self.workspace, exist_ok=True)
        
    def _safe_path(self, target):
        path = os.path.abspath(os.path.join(self.workspace, target))
        if not path.startswith(self.workspace):
            raise Exception("Security violation: path traversal outside workspace")
        return path

    def execute(self, action, caller="unknown"):
        if caller != "qwen_agent":
            raise Exception("❌ Execution blocked: Only Qwen agent can execute actions")
            
        print("SOURCE: QWEN_AGENT")
        print("ACTION:", action)
        
        action_type = action.get("action_type")
        target = action.get("target", "")
        content = action.get("content", "")
        
        try:
            if action_type == "WRITE_FILE":
                path = self._safe_path(target)
                with open(path, "w") as f:
                    f.write(content)
                return {"status": "SUCCESS", "message": f"Wrote {len(content)} bytes to {target}"}
                
            elif action_type == "RUN_COMMAND":
                cmd_str = action.get("command") or target
                cmd = f"cd {self.workspace} && {cmd_str}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return {
                    "status": "SUCCESS" if result.returncode == 0 else "FAIL",
                    "stdout": result.stdout[:2000], 
                    "stderr": result.stderr[:2000],
                    "exit_code": result.returncode
                }
                
            elif action_type == "RUN_BACKGROUND_COMMAND":
                cmd_str = action.get("command") or target
                cmd = f"cd {self.workspace} && {cmd_str}"
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                import time
                time.sleep(2) # Give it time to launch
                return {
                    "status": "SUCCESS",
                    "pid": process.pid,
                    "message": "Process successfully spawned in background."
                }
                
            elif action_type == "READ_FILE":
                path = self._safe_path(target)
                if not os.path.exists(path):
                    return {"status": "FAIL", "message": f"{target} does not exist."}
                with open(path, "r") as f:
                    return {"status": "SUCCESS", "content": f.read()[:2000]}
                    
            elif action_type == "LIST_FILES":
                files = os.listdir(self.workspace)
                return {"status": "SUCCESS", "files": files}
                
            elif action_type == "PATCH_CODE":
                path = self._safe_path(target)
                if not os.path.exists(path):
                    return {"status": "FAIL", "message": f"{target} does not exist for patching."}
                
                original_content = ""
                with open(path, "r") as f:
                    original_content = f.read()
                    
                import json
                try:
                    if isinstance(content, str):
                        try:
                            patch_data = json.loads(content)
                        except:
                            return {"status": "FAIL", "message": "INVALID FORMAT: content must be JSON payload"}
                    else:
                        patch_data = content
                        
                    patch_type = patch_data.get("type", "")
                    payload = patch_data.get("payload", "")
                    
                    if patch_type == "FULL_REWRITE":
                        new_content = payload if isinstance(payload, str) else json.dumps(payload)
                    elif patch_type == "SEARCH_REPLACE":
                        if isinstance(payload, dict):
                            search_str = payload.get("search", "")
                            replace_str = payload.get("replace", "")
                        else:
                            return {"status": "FAIL", "message": "INVALID FORMAT: SEARCH_REPLACE payload must be a dict with search/replace keys."}
                            
                        if search_str and search_str in original_content:
                            new_content = original_content.replace(search_str, replace_str, 1)
                        else:
                            return {"status": "FAIL", "message": "Search match not found. Escalate to FULL_REWRITE."}
                    else:
                        return {"status": "FAIL", "message": "INVALID FORMAT: type must be FULL_REWRITE or SEARCH_REPLACE."}
                        
                except Exception as e:
                    return {"status": "FAIL", "message": f"INVALID FORMAT: Failed to process patch: {str(e)}"}
                    
                # APPLY PATCH
                with open(path, "w") as f:
                    f.write(new_content)
                    
                # DPSE SYNTAX CHECK
                if path.endswith(".py"):
                    chk = subprocess.run(f"python3 -m py_compile {path}", shell=True, capture_output=True, text=True)
                    if chk.returncode != 0:
                        # REVERT
                        with open(path, "w") as f:
                            f.write(original_content)
                        return {"status": "FAIL", "message": f"SYNTAX ERROR. File reverted. Escalate to FULL_REWRITE. Error: {chk.stderr[:500]}"}
                        
                return {"status": "SUCCESS", "message": f"Code patch applied successfully via {patch_type}"}
                
            elif action_type == "COMPLETE":
                return {"status": "SUCCESS", "message": "Triggering ChatGPT Completion Validation"}
                
            else:
                return {"status": "IGNORED", "message": f"Unknown action type: {action_type}"}
                
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
