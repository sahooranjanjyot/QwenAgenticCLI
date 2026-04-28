import json

raw_text = """[
  {
    "action_type": "WRITE_FILE",
    "target": "main.py",
    "content": "foo"
  }
]"""

try:
    parsed = json.loads(raw_text)
    print("Parsed!")
except Exception as e:
    print(f"Error: {e}")
