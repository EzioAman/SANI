import subprocess

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip() if result.stdout else result.stderr.strip()
    except Exception as e:
        return f"Error executing command: {e}"
