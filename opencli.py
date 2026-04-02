import sys, time, os, re
import subprocess

try:
    import readline # This safely magically natively fixes cursor Left/Right tracking & Up/Down user history!
except ImportError:
    pass

try:
    import colorama, requests
    from colorama import Fore, Style
    colorama.init(autoreset=True)
except ImportError:
    sys.stdout.write("Installing local AI network packages...\n")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama", "requests", "-q"])
    import colorama, requests
    from colorama import Fore, Style
    colorama.init(autoreset=True)

def clear(): sys.stdout.write("\033c")

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5-coder:32b"

system_prompt = f"""You are OpenCLI, an autonomous agentic AI natively running on the user's macOS laptop terminal via Ollama.
You are powered by the {MODEL} intelligence engine.
Your purpose is to help the user by actively examining their files, modifying their code, and completely executing their instructions automatically without forcing them to type commands.

To execute a raw bash command directly on their exact Mac terminal, rigidly print the command wrapped strictly in <bash> tags. 
Examples:
<bash>mkdir new_project</bash>
<bash>ls -la ~/Desktop</bash>
<bash>cat main.py</bash>

As soon as you print that specific tag, my Python hook will instantly silently intercept it, officially run it physically on the Mac processor, and feed the raw stdout back directly to you internally in the next logic turn! You can run as many chained commands back-to-back as you structurally need to fulfill the user's specific request.

CRITICAL RULES:
1. ONLY utilize one single <bash> tag block per response!
2. Do NOT use standard markdown backticks for execution. Use <bash> exactly as mathematically shown.
3. If you do not explicitly need to run a native system command, simply answer the user politely normally."""

ollama_history = [{"role": "system", "content": system_prompt}]
ui_history = [{"role": "system", "content": f"Welcome to the OpenCLI Autonomous Agent! Live-connected natively to {MODEL}."}]

clear()
while True:
    print(f"{Fore.CYAN}{Style.BRIGHT}╭──────────────────────────────────────────────────────────╮")
    print(f"│ 🧠 OpenCLI Autonomous Agent (Qwen Local Engine)          │")
    print(f"│ You can now instruct me to physically change your system!│")
    print(f"╰──────────────────────────────────────────────────────────╯{Style.RESET_ALL}\n")

    for msg in ui_history:
        if msg['role'] == 'user':
            print(f"{Fore.GREEN}{Style.BRIGHT}❯ You: {Style.RESET_ALL}{Fore.WHITE}{msg['content']}\n")
        elif msg['role'] == 'system':
            print(f"{Fore.YELLOW}{Style.BRIGHT}💻 System: {Style.RESET_ALL}{Fore.WHITE}{msg['content']}\n")
        elif msg['role'] == 'assistant_cmd':
            print(f"{Fore.BLUE}{Style.BRIGHT}⚙️  Executing: {Style.RESET_ALL}{Fore.CYAN}{msg['content']}\n")
        elif msg['role'] == 'cmd_output':
            print(f"{Fore.LIGHTBLACK_EX}Output:\n{msg['content'][:1500]}{'...' if len(msg['content'])>1500 else ''}\n{Style.RESET_ALL}")
        elif msg['role'] == 'assistant':
            print(f"{Fore.MAGENTA}{Style.BRIGHT}✨ Qwen Agent: {Style.RESET_ALL}{Fore.WHITE}{msg['content']}\n")
    
    print(f"{Fore.CYAN}{Style.BRIGHT}✏️  Instruct me (or /exit): {Style.RESET_ALL}", end="", flush=True)
    try:
        user_input = input().strip()
    except (KeyboardInterrupt, EOFError):
        break
    
    if user_input.lower() in ('/exit', 'quit', 'exit'):
        break
    
    if user_input:
        ui_history.append({"role": "user", "content": user_input})
        ollama_history.append({"role": "user", "content": user_input})
        clear()

        # The Autonomous Agent Decision Loop!
        while True:
            print(f"\n{Fore.CYAN}✨ [Qwen {MODEL} is logically calculating locally...]...{Style.RESET_ALL}")
            
            payload = {"model": MODEL, "messages": ollama_history, "stream": False}
            try:
                response = requests.post(OLLAMA_URL, json=payload).json()
                ai_text = response['message']['content']
                ollama_history.append({"role": "assistant", "content": ai_text})
                
                # Check securely if Qwen natively decided it crucially logically needs to physically execute a bash command!
                bash_match = re.search(r"<bash>(.*?)</bash>", ai_text, re.DOTALL)
                
                if bash_match:
                    command = bash_match.group(1).strip()
                    ui_history.append({"role": "assistant_cmd", "content": command})
                    clear()
                    print(f"\n{Fore.BLUE}⚙️  [Physically Running Command on your Mac Processor]: {command}{Style.RESET_ALL}")
                    
                    try:
                        # THE RAW AGENTIC EXECUTION
                        cmd_output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
                        if not cmd_output.strip(): 
                            cmd_output = "[Command executed flawlessly with no visible output data.]"
                    except subprocess.CalledProcessError as e:
                        cmd_output = f"[Command Failed with Native Error Code {e.returncode}]:\n{e.output}"
                    
                    ui_history.append({"role": "cmd_output", "content": cmd_output})
                    ollama_history.append({"role": "user", "content": f"Terminal Output from your local Mac command:\n{cmd_output}\nWhat is your next step?"})
                    continue 
                else:
                    ui_history.append({"role": "assistant", "content": ai_text.strip()})
                    break 
                    
            except Exception as e:
                ui_history.append({"role": "system", "content": f"Ollama Connection Failed: Ensure Ollama is running. (Error: {str(e)})"})
                break
        
        clear()
