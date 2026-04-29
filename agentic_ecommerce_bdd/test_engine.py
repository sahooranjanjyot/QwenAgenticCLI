import subprocess

def run_tests():
    results = {
        "all_pass": False,
        "details": {}
    }

    import os
    if not os.path.exists("features/store.feature"):
        results["details"]["error"] = "Waiting for you to create features/store.feature"
        return results
        
    if not os.path.exists("main.py"):
        results["details"]["error"] = "Waiting for you to create main.py"
        return results

    try:
        # Run BDD tests using behave
        process = subprocess.run(["behave"], capture_output=True, text=True)
        output = process.stdout + "\n" + process.stderr
        results["details"]["behave_output"] = output

        if process.returncode == 0 and "passed" in output and "0 features passed" not in output:
            results["all_pass"] = True
    except Exception as e:
        results["details"]["error"] = str(e)

    return results
