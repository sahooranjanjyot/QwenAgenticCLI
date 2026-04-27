import json

class Memory:
    def __init__(self):
        self.history = []
        self.state = {
            "file_created": False,
            "script_executed": False,
            "output_written": False
        }
        
    def add_interaction(self, role, content):
        self.history.append({"role": role, "content": content})
        
    def get_qwen_history(self):
        return self.history
        
    def get_history_summary(self):
        return [item for item in self.history if item['role'] != 'system']

    def get_context(self):
        return "Return ONLY next step as JSON."
        
    def __str__(self):
        return json.dumps(self.get_history_summary())
