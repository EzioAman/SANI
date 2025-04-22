import time
import subprocess
import os
import json
import psutil
from gpt4all import GPT4All

# Paths
BASE_DIR = "E:/SANI AI/Code/"
MEMORY_FILES = {
    "general": os.path.join(BASE_DIR, "memory_general.json"),
    "morfit2409": os.path.join(BASE_DIR, "memory_morfit2409.json"),
    "naveenjha": os.path.join(BASE_DIR, "memory_bhaisasur.json"),
    "qwerty": os.path.join(BASE_DIR, "memory_qwerty.json"),
}
MODEL_PATH = "E:\SANI AI\GGUF\mistral-7b-instruct-v0.1.Q4_0.gguf"

# Load memory from file (if exists)
def load_memory(user_type="general"):
    file_path = MEMORY_FILES[user_type]
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {"name": None, "projects": {}, "general_chat": []}

# Save memory to file
def save_memory(memory, user_type="general"):
    with open(MEMORY_FILES[user_type], "w") as f:
        json.dump(memory, f, indent=4)

# Initialize Model
model = GPT4All(MODEL_PATH)

# Default User Memory
current_user = "general"
memory = load_memory(current_user)
current_project = None
admin_users = {"morfit2409": 3, "naveenjha": 2, "qwerty": 1}  # Priority levels


def get_system_info():
    """Retrieves system memory info"""
    total_memory = round(psutil.virtual_memory().total / (1024 ** 3), 2)  # GB
    available_memory = round(psutil.virtual_memory().available / (1024 ** 3), 2)  # GB
    return f"Total RAM: {total_memory} GB | Available RAM: {available_memory} GB"


def type_response(text):
    """Simulates typing effect"""
    for char in text:
        print(char, end="", flush=True)
        time.sleep(0.02)
    print()


def execute_raspberry_command(command):
    """Executes system commands on Raspberry Pi"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip() if result.stdout else result.stderr.strip()
    except Exception as e:
        return f"Error executing command: {str(e)}"


def show_help():
    """Displays command list"""
    print("\n🔹 SANI COMMANDS:")
    print("  - help                  → Show this command menu")
    print("  - start project <name>  → Start a new project")
    print("  - show me all projects  → View saved projects")
    print("  - switch to <project>   → Switch to a project")
    print("  - project done          → Erase project memory (password required)")
    print("  - run <command>         → Execute Raspberry Pi command")
    print("  - reset memory          → Erase all memory (password required)")
    print("  - show memory           → Check system memory usage")
    print("  - end                   → Exit SANI AI\n")


def authenticate_admin(command):
    global current_user, memory
    _, entered_pass = command.split(" -", 1)
    entered_pass = entered_pass.strip()
    if entered_pass in admin_users:
        current_user = entered_pass
        memory = load_memory(current_user)
        print(f"🔹 SANI: Admin access granted to {current_user}. ✅")
    else:
        print("🔹 SANI: Invalid admin credentials. ❌")


print("✅ SANI AI is ready. Type 'help' to see available commands.")

while True:
    prompt = input("\nYou: ").strip()

    # Exit condition
    if prompt.lower() == "end":
        print("🔹 SANI: Goodbye! Have a great day. 😊")
        save_memory(memory, current_user)
        break

    # Help command
    if prompt.lower() == "help":
        show_help()
        continue

    # Admin authentication
    if prompt.lower().startswith("admin -"):
        authenticate_admin(prompt)
        continue

    # Show system memory
    if prompt.lower() == "show memory":
        print("🔹 SANI:", get_system_info())
        continue

    # Show all projects
    if prompt.lower() == "show me all projects":
        if memory["projects"]:
            print("\n🔹 Active Projects:")
            for idx, proj in enumerate(memory["projects"], start=1):
                print(f"  {idx}. {proj}")
        else:
            print("🔹 SANI: No active projects found.")
        continue

    # Switch projects
    if prompt.lower().startswith("switch to "):
        new_project = prompt[10:].strip()
        if new_project in memory["projects"]:
            current_project = new_project
            print(f"🔹 SANI: Switched to project '{current_project}'.")
        else:
            print(f"🔹 SANI: Project '{new_project}' not found.")
        continue

    # Reset all memory
    if prompt.lower() == "reset memory":
        password = input("Enter password to reset all memory: ").strip()
        if password == "aman_reset":
            memory = {"name": None, "projects": {}, "general_chat": []}
            current_project = None
            save_memory(memory, current_user)
            print("🔹 SANI: All memory erased successfully! ✅")
        else:
            print("🔹 SANI: Incorrect password. ❌")
        continue

    # Start a project
    if prompt.lower().startswith("start project "):
        current_project = prompt[14:].strip()
        if current_project:
            if current_project not in memory["projects"]:
                memory["projects"][current_project] = []
            print(f"🔹 SANI: Project '{current_project}' started.")
        continue

    # General Chat
    conversation = "\n".join(memory["general_chat"]) + f"\nUser: {prompt}\nSANI:"
    response = model.generate(conversation, max_tokens=200).strip()
    memory["general_chat"].append(f"User: {prompt}")
    memory["general_chat"].append(f"SANI: {response}")

    # Save memory updates
    save_memory(memory, current_user)

    # Display response with typing effect
    print("🔹 SANI:", end=" ")
    type_response(response)
