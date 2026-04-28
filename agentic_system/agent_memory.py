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

    def get_last(self):
        return self.history[-1] if self.history else None

    def get_last_n(self, n):
        return self.history[-n:] if self.history else []

    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})

    def get_all(self):
        return self.history
