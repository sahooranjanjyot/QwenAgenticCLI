import re
import json

def extract_all_json(raw_text):
    # Try fully decoding first
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except:
        pass

    # Find the outermost braces
    start_idx = raw_text.find('{')
    end_idx = raw_text.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return [json.loads(raw_text[start_idx:end_idx+1])]
        except:
            pass

    # If all fails, return empty list
    return []

def normalize_task(task):
    if "task" in task and isinstance(task["task"], dict):
        task = task["task"]

    # Already valid
    if "type" in task:
        if "file" in task and "content" in task and "files_to_modify" not in task:
            task["files_to_modify"] = [{"path": task["file"], "content": task["content"]}]
        if "command" in task and "commands_to_run" not in task:
            task["commands_to_run"] = [task["command"]]
        return task

    # CASE 1 — Qwen summary format (MOST IMPORTANT)
    if "details" in task:
        details = task["details"]
        if "file_created" in details:
            return {
                "type": "DEVELOP",
                "file": details["file_created"],
                "content": details.get("content", ""),
                "files_to_modify": [{"path": details["file_created"], "content": details.get("content", "")}]
            }
        if "command" in details:
            return {
                "type": "TEST",
                "command": details["command"],
                "commands_to_run": [details["command"]]
            }

    # CASE 2 — execution output block
    if "output" in task and "file_written" not in task and "command" not in task and "status" in task:
        # Sometimes Qwen returns {"task": "run", "output": "..."} without the command itself.
        # We can just check the task name.
        if "run" in task.get("task", "") or "execute" in task.get("task", ""):
             cmd = "python hello_world.py" # infer generic python run
             return {
                 "type": "TEST",
                 "command": cmd,
                 "commands_to_run": [cmd]
             }

    # CASE 3 — file write output
    if "file_written" in task or "output_content" in task or "content_written" in task or "file_name" in task:
        filename = task.get("file_written", task.get("file_name", ""))
        content = task.get("content", task.get("output_content", task.get("content_written", "")))
        if filename:
             # we check if it is purely a file creation
             if task.get("step") == "create_file" or "create" in task.get("task", ""):
                 return {
                     "type": "DEVELOP",
                     "file": filename,
                     "content": content,
                     "files_to_modify": [{"path": filename, "content": content}]
                 }
                 
             # else it's a file write of an output
             if content:
                 cmd = f"echo \"{content}\" > {filename}"
                 return {
                     "type": "TEST",
                     "command": cmd,
                     "commands_to_run": [cmd]
                 }

    # CASE 4 — command-based
    if "command" in task:
        return {
            "type": "TEST",
            "command": task["command"],
            "commands_to_run": [task["command"]]
        }
        
    # Legacy CASE - "step" / "action" / "next_step" mapping
    if "step" in task or "action" in task or "next_step" in task:
        step_str = str(task.get("step", task.get("next_step", "")))
        action_str = str(task.get("action", "")).lower()
        
        if step_str == "create_file" or "file_creation" in action_str or "create" in action_str or "write" in action_str:
            fname = task.get("file_name", task.get("filename", "math_utils.py"))
            fcontent = task.get("content", task.get("file_content", ""))
            return {
                "type": "DEVELOP",
                "file": fname,
                "content": fcontent,
                "files_to_modify": [{"path": fname, "content": fcontent}]
            }
            
        if step_str == "run_script" or "run" in action_str or step_str == "execute_script":
            cmd = f"python {task.get('script_name', task.get('file_name', 'hello_world.py'))}"
            return {
                "type": "TEST",
                "command": cmd,
                "commands_to_run": [cmd]
            }

    # CASE 5 — fallback ONLY if nothing matches
    print("⚠️ WARNING: Using fallback — unknown Qwen format:", task)

    return {
        "type": "TEST",
        "command": "echo 'Fallback execution triggered'",
        "commands_to_run": ["echo 'Fallback execution triggered'"],
        "is_fallback": True
    }
