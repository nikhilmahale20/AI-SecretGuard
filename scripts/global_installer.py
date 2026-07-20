#global_installer.py
import os
import shutil
import subprocess
import stat
import sys

def setup_global_sentinel():
    print(">> Initializing Neural-Sentinel Global Setup...")

    # 1. PATHS
    # The source files are relative to this script
    installer_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(installer_dir)
    
    # The destination is the hidden home folder
    home = os.path.expanduser("~")
    sentinel_home = os.path.join(home, ".neural_sentinel")
    hooks_dest = os.path.join(sentinel_home, "hooks")
    core_dest = os.path.join(sentinel_home, "neural_sentinel_core")

    # 2. CREATE DIRECTORIES
    os.makedirs(hooks_dest, exist_ok=True)
    os.makedirs(core_dest, exist_ok=True)

    # 3. DEPLOY THE BRAIN (Audit Engine & Entropy Logic)
    src_engine = os.path.join(project_root, "neural_sentinel_core", "audit_engine.py")
    src_logic = os.path.join(project_root, "neural_sentinel_core", "entropy_logic.py")
    
    dst_engine = os.path.join(core_dest, "audit_engine.py")
    dst_logic = os.path.join(core_dest, "entropy_logic.py")
    
    if os.path.exists(src_engine) and os.path.exists(src_logic):
        shutil.copy2(src_engine, dst_engine)
        shutil.copy2(src_logic, dst_logic)
        print(f"✅ Core Logic deployed to: {core_dest}")
    else:
        print(f"❌ ERROR: Could not find Python core files.")
        return
    
    # 4. DEPLOY THE TRIGGER (Hook)
    # Note: Git hooks must be named 'pre-commit' (no .sh extension)
    src_hook = os.path.join(installer_dir, "pre_commit_hook.sh")
    dst_hook = os.path.join(hooks_dest, "pre-commit")

    if os.path.exists(src_hook):
        shutil.copy2(src_hook, dst_hook)
        # Make it executable (chmod +x)
        st = os.stat(dst_hook)
        os.chmod(dst_hook, st.st_mode | stat.S_IEXEC)
        print(f"✅ Hook script deployed to: {dst_hook}")
    else:
        print(f"❌ ERROR: Could not find {src_hook}")
        return

    # 5. ACTIVATE GIT CONFIG
    try:
        subprocess.run(["git", "config", "--global", "core.hooksPath", hooks_dest], check=True)
        print("✅ Git Global Config updated.")
    except Exception as e:
        print(f"❌ Git Config Failed: {e}")
        return

    print("\n🚀 Neural Sentinel is now protecting ALL repositories on this machine!")

if __name__ == "__main__":
    setup_global_sentinel()