# audit_engine.py (Updated)
import os
import subprocess
import sys
import tree_sitter_javascript as tsjavascript
import tree_sitter_python as tspython # Added for Python support
from tree_sitter import Language, Parser, Query, QueryCursor
from transformers import pipeline
from entropy_logic import is_high_entropy

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# --- USE YOUR FINE-TUNED BRAIN ---
print("🧠 [Neural Sentinel] Initializing Fine-Tuned CodeBERT...")
MODEL_PATH = os.path.join(os.path.expanduser("~"), ".neural_sentinel", "neural_sentinel_core", "neural-sentinel-finetuned")

# Fallback to local path if global path isn't setup yet
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = "./neural-sentinel-finetuned"

code_analyzer = pipeline("text-classification", model=MODEL_PATH)

JS_LANGUAGE = Language(tsjavascript.language())
PY_LANGUAGE = Language(tspython.language())

def scan_for_secrets():
    staged_files = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'], 
        capture_output=True, text=True
    ).stdout.splitlines()

    if not staged_files:
        return 0

    found_issues = False
    parser = Parser()

    for file_path in staged_files:
        # Determine language
        if file_path.endswith((".js", ".ts")):
            lang = JS_LANGUAGE
            query_str = "(variable_declarator name: (identifier) @name value: (string) @val)"
        elif file_path.endswith(".py"):
            lang = PY_LANGUAGE
            query_str = "(assignment left: (identifier) @name right: (string) @val)"
        else:
            continue

        parser.language = lang
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        tree = parser.parse(bytes(source_code, "utf8"))
        query = Query(lang, query_str)
        cursor = QueryCursor(query)
        
        for match in cursor.matches(tree.root_node):
            capture_dict = match[1]
            var_name = capture_dict["name"][0].text.decode("utf8")
            val = capture_dict["val"][0].text.decode("utf8").strip("'\"")

            # 2. Hybrid Check (Entropy + AI)
            is_random, _ = is_high_entropy(val)
            context = f"{var_name} = '{val}'"
            result = code_analyzer(context)[0]
            
            # Using your established 0.95 threshold
            if result['score'] > 0.95 or (result['score'] > 0.70 and is_random):
                print(f"\n[Neural Sentinel] 🛑 COMMIT BLOCKED: Secret in {file_path}")
                print(f"   Variable: {var_name} | Confidence: {result['score']:.2%}")
                found_issues = True

    return 1 if found_issues else 0

if __name__ == "__main__":
    sys.exit(scan_for_secrets())