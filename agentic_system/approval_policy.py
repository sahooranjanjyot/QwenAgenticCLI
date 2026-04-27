import re

class ApprovalPolicy:
    @staticmethod
    def is_approved(command):
        # Auto-deny rules
        deny_tokens = ["sudo ", "rm -rf", "rm -r ", "chown ", "chmod 777"]
        for token in deny_tokens:
            if token in command:
                return False, f"Command denied due to token: {token}"
                
        # Must not access secrets
        if "cat ~/.ssh" in command or "cat ~/.aws" in command or "env" in command:
             return False, "Command denied due to credentials access"

        # The instructions say "Auto-approve python, mvn test, file creation, curl, etc."
        # This basically means everything not in deny list is approved.
        return True, "Auto-approved"
