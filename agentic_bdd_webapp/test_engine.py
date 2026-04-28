import subprocess

def run_tests():
    results = {
        "all_pass": False,
        "details": {}
    }

    try:
        # Run BDD tests using behave
        process = subprocess.run(["behave"], capture_output=True, text=True)
        output = process.stdout + "\n" + process.stderr
        results["details"]["behave_output"] = output

        # If behave succeeds, exit code is 0
        if process.returncode == 0 and "passed" in output and "0 features passed" not in output:
            results["all_pass"] = True
        else:
            if "0 features passed" in output:
                results["details"]["error"] = "No features were run! You must write the .feature files first."
            
    except Exception as e:
        results["details"]["error"] = str(e)

    return results
