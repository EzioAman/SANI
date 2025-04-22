import time
import os
import argparse
import logging
from gpt4all import GPT4All
from memory_handler import update_memory, get_recent_history, reset_memory
from sheets_api import update_google_sheets, reset_google_sheets, find_next_empty_row
from command_handler import execute_command

# Configure logging
LOG_DIR = "E:/SANI AI/Logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(filename=os.path.join(LOG_DIR, "sani.log"), level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Set up argument parser
parser = argparse.ArgumentParser()
parser.add_argument("--model_path", required=True, help="Path to the model file")
args = parser.parse_args()
MODEL_PATH = args.model_path

# Force CPU mode
os.environ["LLAMA_FORCE_CPU"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["USE_CUDA"] = "0"

class SANI:
    def __init__(self, model_path):
        try:
            self.model = GPT4All(model_path, allow_download=False)
        except Exception as e:
            logging.error(f"❌ Error initializing model: {e}")
            self.model = None

    def type_response(self, text):
        """Simulates typing effect."""
        for char in text:
            print(char, end="", flush=True)
            time.sleep(0.02)
        print()

    def chat(self, user_input):
        """Handles conversation, memory, and commands."""
        if user_input.lower() == "reset memory":
            return reset_memory()

        if user_input.lower() == "reset online memory":
            return reset_google_sheets("Important Data")

        if user_input.lower().startswith("run "):
            command = user_input[4:].strip()
            return execute_command(command)

        if user_input.lower().startswith("save this to the database:"):
            data = user_input[len("save this to the database:"):].strip()
            update_memory("important_data", data)
            print("🔹 SANI: Information saved locally. Do you want to update the online database? (yes/no)")
            confirm = input("You: ").strip().lower()
            if confirm == "yes":
                return update_google_sheets("Important Data", data)
            else:
                return "✅ Data stored locally only."

        history = get_recent_history(limit=5)
        conversation = f"{history}\nUser: {user_input}\nSANI:"
        try:
            response = self.model.generate(conversation, max_tokens=200).strip()
        except Exception as e:
            response = f"❌ Error generating response: {e}"
            logging.error(response)

        update_memory("chat_history", {"user": user_input, "sani": response})
        return response

if __name__ == "__main__":
    sani = SANI(MODEL_PATH)
    if sani.model is None:
        print("❌ Error: Model failed to initialize.")
    else:
        print("✅ SANI AI is ready. Type 'exit' to stop.")

    try:
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() == "exit":
                print("🔹 SANI: Goodbye!")
                break
            response = sani.chat(user_input)
            print("🔹 SANI:", end=" ")
            sani.type_response(response)
    except KeyboardInterrupt:
        print("\n🔹 SANI: Exiting safely. Goodbye!")
