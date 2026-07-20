#pre_commit_hook.sh
#!/usr/bin/env bash

# Path to your global Python logic
AUDIT_ENGINE="$HOME/.neural_sentinel/neural_sentinel_core/audit_engine.py"

# Run the Python audit (using 'python' for Windows)
python "$AUDIT_ENGINE"

# Capture the result (exit 0 = success, exit 1 = secret found)
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "❌ [Neural-Sentinel] Commit Blocked! High-risk data detected."
  exit 1
fi

exit 0