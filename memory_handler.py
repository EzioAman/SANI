import json
import os

MEMORY_FILE = "E:/SANI AI/Data/memory.json"

# Ensure memory file exists
if not os.path.exists("E:/SANI AI/Data"):
    os.makedirs("E:/SANI AI/Data")

if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w") as f:
        json.dump({"chat_history": [], "important_data": []}, f, indent=4)

def update_memory(key, value):
    """Update the memory file with new data."""
    memory = load_memory()
    
    # Ensure the key exists in memory
    if key not in memory:
        memory[key] = []

    # Ensure it's a list before appending
    if isinstance(memory[key], list):
        memory[key].append(value)
    
    save_memory(memory)

def load_memory():
    """Load memory from the JSON file."""
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"chat_history": [], "important_data": []}

def save_memory(memory):
    """Save memory to the JSON file."""
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

def update_memory(key, value):
    """Update the memory file with new data."""
    memory = load_memory()
    
    # Ensure the key exists in memory
    if key not in memory:
        memory[key] = []

    # Ensure it's a list before appending
    if isinstance(memory[key], list):
        memory[key].append(value)
    
    save_memory(memory)

def get_recent_history(limit=5):
    """Retrieve the last few entries from chat history."""
    memory = load_memory()
    history = memory.get("chat_history", [])
    return "\n".join([f"User: {entry['user']}\nSANI: {entry['sani']}" for entry in history[-limit:]])

def reset_memory():
    """Erase all stored memory."""
    save_memory({"chat_history": [], "important_data": []})
    return "✅ Memory has been reset successfully."
