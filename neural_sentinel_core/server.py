# server.py
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import json

# --- Tree-sitter Imports ---
import tree_sitter_javascript as tsjavascript
import tree_sitter_python as tspython
import tree_sitter_java as tsjava
import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser, Query, QueryCursor

from transformers import pipeline
from entropy_logic import is_high_entropy
from fastapi.middleware.cors import CORSMiddleware

# Import database logic
from database import init_db, SessionLocal, AuditLog
from sqlalchemy.orm import Session

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3" 

app = FastAPI(title="Neural-Sentinel Context Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

print("🧠 Loading CUSTOM Fine-Tuned Neural-Sentinel Brain...")
code_analyzer = pipeline("text-classification", model="./neural-sentinel-finetuned")

# --- Initialize Language Grammars ---
JS_LANGUAGE = Language(tsjavascript.language())
PY_LANGUAGE = Language(tspython.language())
JAVA_LANGUAGE = Language(tsjava.language())
C_LANGUAGE = Language(tsc.language())
CPP_LANGUAGE = Language(tscpp.language())

class CodePayload(BaseModel):
    file_name: str
    code_content: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------
# AST QUERY 1: Secret Assignments (SecretBench Claim)
# ---------------------------------------------------------
def get_ast_assignments(file_name, source_code, parser):
    if file_name.endswith((".js", ".ts")):
        parser.language = JS_LANGUAGE
        query = Query(JS_LANGUAGE, "(variable_declarator name: (identifier) @var_name value: (string) @var_value)")
    elif file_name.endswith(".py"):
        parser.language = PY_LANGUAGE
        query = Query(PY_LANGUAGE, "(assignment left: (identifier) @var_name right: (string) @var_value)")
    elif file_name.endswith(".java"):
        parser.language = JAVA_LANGUAGE
        query = Query(JAVA_LANGUAGE, "(variable_declarator name: (identifier) @var_name value: (string_literal) @var_value)")
    elif file_name.endswith((".c", ".cpp")):
        lang = C_LANGUAGE if file_name.endswith(".c") else CPP_LANGUAGE
        parser.language = lang
        query = Query(lang, "(init_declarator declarator: (identifier) @var_name value: (string_literal) @var_value)")
    else:
        return []

    tree = parser.parse(bytes(source_code, "utf8"))
    cursor = QueryCursor(query)
    matches = cursor.matches(tree.root_node)
    
    assignments = []
    for match in matches:
        capture_dict = match[1] 
        name_nodes = capture_dict.get("var_name", [])
        val_nodes = capture_dict.get("var_value", [])
        if name_nodes and val_nodes:
            assignments.append({
                "type": "SECRET",
                "variable_name": name_nodes[0].text.decode("utf8").strip("'\""),
                "secret_value": val_nodes[0].text.decode("utf8").strip("'\""),
                "line": name_nodes[0].start_point[0] + 1
            })
    return assignments

# ---------------------------------------------------------
# AST QUERY 2: Logical Flaws / Loops (Big-Vul Claim)
# ---------------------------------------------------------
def get_ast_loops(file_name, source_code, parser):
    """Extracts while/for loops to analyze for logical flaws like infinite loops."""
    if file_name.endswith((".js", ".ts")):
        parser.language = JS_LANGUAGE
        query = Query(JS_LANGUAGE, "(while_statement) @loop (for_statement) @loop")
    elif file_name.endswith(".py"):
        parser.language = PY_LANGUAGE
        query = Query(PY_LANGUAGE, "(while_statement) @loop (for_statement) @loop")
    elif file_name.endswith(".java"):
        parser.language = JAVA_LANGUAGE
        query = Query(JAVA_LANGUAGE, "(while_statement) @loop (for_statement) @loop")
    elif file_name.endswith((".c", ".cpp")):
        lang = C_LANGUAGE if file_name.endswith(".c") else CPP_LANGUAGE
        parser.language = lang
        query = Query(lang, "(while_statement) @loop (for_statement) @loop")
    else:
        return []

    tree = parser.parse(bytes(source_code, "utf8"))
    cursor = QueryCursor(query)
    matches = cursor.matches(tree.root_node)
    
    loops = []
    for match in matches:
        capture_dict = match[1]
        loop_nodes = capture_dict.get("loop", [])
        if loop_nodes:
            # We take the first 200 chars of the loop block as the context window
            loop_text = loop_nodes[0].text.decode("utf8")[:200]
            loops.append({
                "type": "LOGICAL_FLAW",
                "variable_name": "Loop Block",
                "secret_value": loop_text, # Reusing this field for the code snippet
                "line": loop_nodes[0].start_point[0] + 1
            })
    return loops

@app.post("/scan-code")
async def scan_code(payload: CodePayload, db: Session = Depends(get_db)):
    print(f"🔍 Scanning: {payload.file_name}")
    try:
        parser = Parser()
        
        # Run both queries
        assignments = get_ast_assignments(payload.file_name, payload.code_content, parser)
        loops = get_ast_loops(payload.file_name, payload.code_content, parser)
        
        all_candidates = assignments + loops
        threats = []
        
        for item in all_candidates:
            var_name = str(item["variable_name"])
            val = str(item["secret_value"])
            
            # --- Secret Scanning Logic ---
            if item["type"] == "SECRET":
                if len(val) < 8: continue
                context_prompt = f"{var_name} = '{val}'"
                result = code_analyzer(context_prompt)[0]
                is_random, entropy_score = is_high_entropy(val)
                
                if result['score'] > 0.95 or (result['score'] > 0.70 and is_random):
                    threats.append({
                        "variable_name": var_name,
                        "secret_value": val,
                        "line": int(item["line"]),
                        "confidence": float(result['score']),
                        "risk_level": "CRITICAL",
                        "threat_type": "Hardcoded Secret"
                    })
                    
            # --- Logical Flaw Scanning Logic (Big-Vul) ---
            elif item["type"] == "LOGICAL_FLAW":
                # Feed the 200-char context window of the loop to CodeBERT
                result = code_analyzer(val)[0]
                
                # If the AI thinks this loop is structurally vulnerable (e.g. > 0.90 confidence)
                if result['score'] > 0.90:
                    threats.append({
                        "variable_name": "Suspicious Loop Control",
                        "secret_value": val[:50] + "...", # Just show a snippet
                        "line": int(item["line"]),
                        "confidence": float(result['score']),
                        "risk_level": "HIGH",
                        "threat_type": "Logical Vulnerability"
                    })
        
        status = "danger" if threats else "safe"
        
        if threats:
            clean_threats_json = json.dumps(threats)
            audit_record = AuditLog(
                file_name=payload.file_name,
                status=status,
                threat_count=len(threats),
                highest_risk="CRITICAL",
                threat_details=clean_threats_json
            )
            db.add(audit_record)
            db.commit()
            print(f"✅ DB Saved. Threats found: {len(threats)}")
        
        return JSONResponse(content={
            "status": status,
            "message": "AI detected threats!" if threats else "Scan Complete",
            "threats": threats
        })

    except Exception as e:
        print(f"❌ BACKEND CRASH: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/audit-logs")
async def get_audit_logs(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    output = []
    for log in logs:
        output.append({
            "id": log.id,
            "file_name": log.file_name,
            "status": log.status,
            "threat_count": log.threat_count,
            "highest_risk": log.highest_risk,
            "details": json.loads(log.threat_details),
            "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
    return output