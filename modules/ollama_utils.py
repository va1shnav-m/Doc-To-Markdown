import subprocess
import time
import requests


from modules.config import OLLAMA_URL, OLLAMA_STARTUP_TIMEOUT


def is_ollama_running():
    try:
        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=2
        )
        return response.status_code == 200

    except requests.RequestException:
        return False


def ensure_ollama_running():

    # Already running
    if is_ollama_running():
        print("Ollama is already running.")
        return True

    print("Ollama is not running. Starting Ollama...")

    try:
        popen_kwargs = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        # Only set CREATE_NO_WINDOW on platforms where it exists (Windows)
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        subprocess.Popen(["ollama", "serve"], **popen_kwargs)

    except Exception as e:
        print(f"Failed to start Ollama: {e}")
        return False

    # Wait for Ollama to become available
    start_time = time.time()

    while time.time() - start_time < STARTUP_TIMEOUT:

        if is_ollama_running():
            print("Ollama started successfully.")
            return True

        time.sleep(1)

    print("Ollama did not start within the timeout.")
    return False