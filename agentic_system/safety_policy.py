def rejects(action):
    if not isinstance(action, dict):
        return True
        
    target = action.get("target", "").lower()
    
    # Auto-deny rules
    deny_list = ["sudo ", "rm -rf", "passwd", "chown", ".aws", "credentials"]
    
    for d in deny_list:
        if d in target:
            print(f"🛑 SAFETY REJECTED: Contains restricted command/target '{d}'")
            return True
            
    return False
