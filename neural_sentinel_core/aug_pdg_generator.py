# aug_pdg_generator.py
import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor
import json

# Initialize Python Language for the PDG generation
PY_LANGUAGE = Language(tspython.language())

class AUG_PDG_Node:
    def __init__(self, node_id, node_type, code_snippet, line_number):
        self.id = node_id
        self.type = node_type
        self.code = code_snippet
        self.line = line_number

class AUG_PDG_Edge:
    def __init__(self, source_id, target_id, edge_type):
        self.source = source_id
        self.target = target_id
        self.edge_type = edge_type  # e.g., "UseDef", "ScopeEnd", "ControlFlow"

def generate_aug_pdg(source_code: str):
    """
    Constructs a lightweight Augmented Program Dependency Graph (AUG-PDG).
    Extracts Data-Flow (UseDef) and Block boundaries (ScopeEnd) to provide
    structural context to the CodeBERT AI model.
    """
    print("🕸️ Constructing Augmented Program Dependency Graph (AUG-PDG)...")
    parser = Parser()
    parser.language = PY_LANGUAGE
    tree = parser.parse(bytes(source_code, "utf8"))

    nodes = {}
    edges = []
    node_counter = 1

    # 1. Query for Variable Definitions (The 'Def' in UseDef)
    def_query = Query(PY_LANGUAGE, "(assignment left: (identifier) @def_name right: (_) @def_val)")
    cursor = QueryCursor(def_query)
    
    definitions = {}
    for match in cursor.matches(tree.root_node):
        def_node = match[1].get("def_name")[0]
        var_name = def_node.text.decode("utf8")
        line = def_node.start_point[0] + 1
        
        # Create PDG Node
        nodes[node_counter] = AUG_PDG_Node(node_counter, "Definition", var_name, line)
        definitions[var_name] = node_counter
        node_counter += 1

    # 2. Query for Variable Usages (The 'Use' in UseDef)
    use_query = Query(PY_LANGUAGE, "(call arguments: (argument_list (identifier) @use_name))")
    cursor = QueryCursor(use_query)
    
    for match in cursor.matches(tree.root_node):
        use_node = match[1].get("use_name")[0]
        var_name = use_node.text.decode("utf8")
        line = use_node.start_point[0] + 1
        
        # If this variable was defined earlier, create a UseDef Edge!
        if var_name in definitions:
            nodes[node_counter] = AUG_PDG_Node(node_counter, "Usage", var_name, line)
            # Create the UseDef Edge mapping the Usage back to its Definition
            edges.append(AUG_PDG_Edge(source_id=node_counter, target_id=definitions[var_name], edge_type="UseDef"))
            node_counter += 1

    # 3. Query for Scope Boundaries (ScopeEnd)
    scope_query = Query(PY_LANGUAGE, "(function_definition name: (identifier) @func_name body: (block) @body)")
    cursor = QueryCursor(scope_query)
    
    for match in cursor.matches(tree.root_node):
        func_node = match[1].get("func_name")[0]
        body_node = match[1].get("body")[0]
        
        func_name = func_node.text.decode("utf8")
        end_line = body_node.end_point[0] + 1
        
        nodes[node_counter] = AUG_PDG_Node(node_counter, "ScopeBoundary", func_name, end_line)
        # Create the ScopeEnd Edge representing the termination of the local context
        edges.append(AUG_PDG_Edge(source_id=node_counter, target_id=node_counter, edge_type="ScopeEnd"))
        node_counter += 1

    # Output the structural representation
    pdg_output = {
        "nodes": [{"id": n.id, "type": n.type, "code": n.code, "line": n.line} for n in nodes.values()],
        "edges": [{"source": e.source, "target": e.target, "edge_type": e.edge_type} for e in edges]
    }
    
    return pdg_output

if __name__ == "__main__":
    # Test the PDG extraction with a sample vulnerable snippet
    sample_code = """
def connect_to_db():
    api_key = "sk_live_123456789"
    print("Connecting...")
    authenticate(api_key)
"""
    graph = generate_aug_pdg(sample_code)
    print(json.dumps(graph, indent=2))