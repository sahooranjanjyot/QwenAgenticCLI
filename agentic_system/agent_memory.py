import json

class AgentMemory:
    def __init__(self):
        self.history = []
        
    def add(self, role, content):
        self.history.append({"role": role, "content": content})
        
    def get_messages(self, limit=20):
        # We can structure the context block for Qwen
        return self.history[-limit:]
        
    def format_history(self):
        ctx = ""
        for item in self.history:
            if item['role'] == "system":
                continue # System is sent separately
            ctx += f"[{item['role'].upper()}]: {item['content']}\n"
        return ctx
