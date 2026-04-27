import os

class WorkspaceManager:
    def __init__(self, base_dir="workspace"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def write_file(self, filepath, content):
        full_path = self.get_absolute_path(filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)

    def read_file(self, filepath):
        full_path = self.get_absolute_path(filepath)
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                return f.read()
        return ""
        
    def get_absolute_path(self, filepath):
        if filepath.startswith("/"):
            return filepath
        return os.path.join(self.base_dir, filepath)
