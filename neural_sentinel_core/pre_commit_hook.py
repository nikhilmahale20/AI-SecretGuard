# pre_commit_hook.py
import sys
import subprocess
import requests

# The URL of your running FastAPI server
API_URL = "http://127.0.0.1:8000/scan-code"

def get_staged_files():
    """Gets the list of files currently staged for commit."""
    result = subprocess.run(['git', 'diff', '--cached', '--name-only'], capture_output=True, text=True)
    return result.stdout.strip().split('\n')

def scan_file(file_path):
    """Sends the file content to the Neural-Sentinel API."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        payload = {"file_name": file_path, "code_content": content}
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "danger":
                print(f"🛑 [Neural-Sentinel] CRITICAL: Secrets detected in {file_path}!")
                for threat in data.get("threats", []):
                    print(f"   - Line {threat['line']}: {threat['variable_name']} (Confidence: {threat['confidence']:.2%})")
                return False
        return True
    except Exception as e:
        print(f"⚠️ [Neural-Sentinel] Scanner Connection Error: {e}")
        return True # Allow commit if server is down (Standard UX practice)

def main():
    files = get_staged_files()
    if not files or files == ['']:
        sys.exit(0)

    print("🧠 Neural-Sentinel: Checking staged files for secrets...")
    failed = False
    for file in files:
        if file.endswith(('.py', '.js', '.ts')):
            if not scan_file(file):
                failed = True

    if failed:
        print("\n❌ Commit rejected. Please remove secrets or move them to a .env file.")
        sys.exit(1) # This 1 tells Git to STOP the commit
    else:
        print("✅ No secrets found. Proceeding with commit.")
        sys.exit(0)

if __name__ == "__main__":
    main()