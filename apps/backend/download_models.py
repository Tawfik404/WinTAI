import sys
import subprocess
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parents[2]
STT_MODEL_DIR = REPO_ROOT / "models" / "stt"

def download_model():
    # Ensure dependencies are installed first so we can import moonshine_voice
    print("Ensuring moonshine-voice is installed in virtual environment...")
    try:
        import moonshine_voice
    except ImportError:
        print("moonshine-voice not found. Installing via pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "moonshine-voice>=0.0.65"], check=True)
        print("Installation complete.")
    
    # Import the official API
    from moonshine_voice import get_model_for_language, ModelArch
    
    # Create target directory
    STT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Requesting official download for medium-streaming-en (this may take a few minutes)...")
    try:
        model_path, model_arch = get_model_for_language(
            wanted_language="en",
            wanted_model_arch=ModelArch.MEDIUM_STREAMING,
            cache_root=STT_MODEL_DIR
        )
        print(f"\nSuccess! Model downloaded and cached at:\n{model_path}")
        print(f"Model Architecture: {model_arch}")
    except Exception as e:
        print(f"\nFailed to download model using official API: {e}")
        raise

if __name__ == "__main__":
    download_model()
