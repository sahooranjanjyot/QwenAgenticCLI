import sys, time, os, re, json
import subprocess

try:
    import colorama, requests, readline
    from colorama import Fore, Style
    colorama.init(autoreset=True)
except ImportError:
    sys.stdout.write("Installing local AI network packages...\n")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama", "requests", "-q"])
    import colorama, requests, readline
    from colorama import Fore, Style
    colorama.init(autoreset=True)

def clear(): sys.stdout.write("\033c")

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5-coder:32b"

system_prompt = f"""You are OpenCLI, an autonomous agentic AI running on macOS via Ollama.
Powered by {MODEL}.
To execute a bash command, wrap it strictly in <bash> tags. 
Examples:
<bash>mkdir temp</bash>
<bash>ls -la</bash>
My Python hook will execute it and send you the stdout. Run ONE command per response. Do not use backticks for commands, only <bash> tags.
"""

ollama_history = [{"role": "system", "content": system_prompt}]
ui_history = [{"role": "system", "content": f"Welcome to the OpenCLI Autonomous Agent! Live-connected to local {MODEL}."}]

clear()
while True:
    print(f"{Fore.CYAN}{Style.BRIGHT}╭──────────────────────────────────────────────────────────╮")
    print(f"│ 🧠 OpenCLI Autonomous Streaming Agent (Qwen Local)       │")
    print(f"╰──────────────────────────────────────────────────────────╯{Style.RESET_ALL}\n")

    for msg in ui_history:
        if msg['role'] == 'user': print(f"{Fore.GREEN}{Style.BRIGHT}❯ You: {Style.RESET_ALL}{Fore.WHITE}{msg['content']}\n")
        elif msg['role'] == 'system': print(f"{Fore.YELLOW}{Style.BRIGHT}💻 System: {Style.RESET_ALL}{Fore.WHITE}{msg['content']}\n")
        elif msg['role'] == 'assistant_cmd': print(f"{Fore.BLUE}{Style.BRIGHT}⚙️  Executing: {Style.RESET_ALL}{Fore.CYAN}{msg['content']}\n")
        elif msg['role'] == 'cmd_output': print(f"{Fore.LIGHTBLACK_EX}Output:\n{msg['content'][:1500]}{'...' if len(msg['content'])>1500 else ''}\n{Style.RESET_ALL}")
        elif msg['role'] == 'assistant': print(f"{Fore.MAGENTA}{Style.BRIGHT}✨ Qwen Agent: {Style.RESET_ALL}{Fore.WHITE}{msg['content']}\n")
    
    print(f"{Fore.CYAN}{Style.BRIGHT}✏️  Instruct me (or /exit): {Style.RESET_ALL}", end="", flush=True)
    try:
        user_input = input().strip()
    except (KeyboardInterrupt, EOFError):
        break
    if user_input.lower() in ('/exit', 'quit', 'exit'): break
    
    if user_input:
        ui_history.append({"role": "user", "content": user_input})
        ollama_history.append({"role": "user", "content": user_input})
        clear()

        # Agent Loop
        while True:
            # Re-print UI because we just cleared it
            print(f"{Fore.CYAN}{Style.BRIGHT}╭──────────────────────────────────────────────────────────╮")
            print(f"│ 🧠 OpenCLI Autonomous Streaming Agent (Qwen Local)       │")
            print(f"╰──────────────────────────────────────────────────────────╯{Style.RESET_ALL}\n")
            for msg in ui_history:
                if msg['role'] == 'user': print(f"{Fore.GREEN}{Style.BRIGHT}❯ You: {Style.RESET_ALL}{Fore.WHITE}{msg['content']}\n")
                elif msg['role'] == 'system': print(f"{Fore.YELLOW}{Style.BRIGHT}💻 System: {Style.RESET_ALL}{Fore.WHITE}{msg['content']}\n")
                elif msg['role'] == 'assistant_cmd': print(f"{Fore.BLUE}{Style.BRIGHT}⚙️  Executing: {Style.RESET_ALL}{Fore.CYAN}{msg['content']}\n")
                elif msg['role'] == 'cmd_output': print(f"{Fore.LIGHTBLACK_EX}Output:\n{msg['content'][:1500]}{'...' if len(msg['content'])>1500 else ''}\n{Style.RESET_ALL}")
                elif msg['role'] == 'assistant': print(f"{Fore.MAGENTA}{Style.BRIGHT}✨ Qwen Agent: {Style.RESET_ALL}{Fore.WHITE}{msg['content']}\n")

            print(f"{Fore.MAGENTA}{Style.BRIGHT}✨ Qwen Agent: {Style.RESET_ALL}", end="", flush=True)
            
            payload = {"model": MODEL, "messages": ollama_history, "stream": True}
            ai_text = ""
            
            try:
                # Watch Qwen type in real-time!
                with requests.post(OLLAMA_URL, json=payload, stream=True) as response:
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            chunk = data.get("message", {}).get("content", "")
                            ai_text += chunk
                            sys.stdout.write(Fore.WHITE + chunk)
                            sys.stdout.flush()
                
                print("\n")
                ollama_history.append({"role": "assistant", "content": ai_text})
                
                # Check for bash commands
                bash_match = re.search(r"<bash>(.*?)</bash>", ai_text, re.DOTALL)
                if bash_match:
                    command = bash_match.group(1).strip()
                    ui_history.append({"role": "assistant_cmd", "content": command})
                    print(f"{Fore.BLUE}⚙️  [Running]: {command}{Style.RESET_ALL}")
                    try:
                        cmd_output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
                        if not cmd_output.strip(): cmd_output = "[Success. No output.]"
                    except subprocess.CalledProcessError as e:
                        cmd_output = f"[Error Code {e.returncode}]:\n{e.output}"
                    
                    ui_history.append({"role": "cmd_output", "content": cmd_output})
                    ollama_history.append({"role": "user", "content": f"Terminal Output:\n{cmd_output}\nWhat is your next step?"})
                    clear()
                    continue 
                else:
                    ui_history.append({"role": "assistant", "content": ai_text.strip()})
                    break 
                    
            except Exception as e:
                ui_history.append({"role": "system", "content": f"Ollama Connection Failed. Error: {str(e)}"})
                break
        clear()
