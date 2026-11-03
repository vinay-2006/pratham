import os
import ast
import json
import re
from pathlib import Path

ROOT_DIR = Path("d:/pratham")
BACKEND_DIR = ROOT_DIR / "backend" / "app"
FRONTEND_DIR = ROOT_DIR / "frontend" / "src"
MIGRATIONS_DIR = ROOT_DIR / "backend" / "migrations"
OUTPUT_DIR = ROOT_DIR / "atlas_data"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_apis():
    api_dir = BACKEND_DIR / "api"
    endpoints = []
    
    if not api_dir.exists():
        return endpoints

    for file in api_dir.glob("*.py"):
        if file.name == "__init__.py": continue
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                                method = decorator.func.attr.upper()
                                path = ""
                                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                    path = decorator.args[0].value
                                
                                endpoints.append({
                                    "file": file.name,
                                    "method": method,
                                    "path": path,
                                    "function": node.name
                                })
    return endpoints

def extract_database():
    tables = []
    if not MIGRATIONS_DIR.exists():
        return tables
        
    create_table_pattern = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([^\s\(]+)", re.IGNORECASE)
    
    for file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            # Simple heuristic
            matches = create_table_pattern.findall(content)
            for m in matches:
                table_name = m.replace('"', '').replace('public.', '')
                if table_name not in [t['name'] for t in tables]:
                    tables.append({
                        "name": table_name,
                        "migration_file": file.name,
                        "columns": [] 
                    })
    return tables

def extract_frontend_routes():
    routes = []
    routes_dir = FRONTEND_DIR / "routes"
    if not routes_dir.exists():
        return routes
        
    for file in routes_dir.glob("*.tsx"):
        routes.append({
            "file": file.name,
            "route": file.name.replace("_app.", "").replace(".tsx", "").replace("__root", "/")
        })
    return routes

def main():
    print("Starting PRATHAM System Atlas Extraction...")
    
    apis = extract_apis()
    with open(OUTPUT_DIR / "api.json", "w", encoding="utf-8") as f:
        json.dump({"endpoints": apis}, f, indent=2)
        
    db = extract_database()
    with open(OUTPUT_DIR / "database.json", "w", encoding="utf-8") as f:
        json.dump({"tables": db}, f, indent=2)
        
    frontend = extract_frontend_routes()
    with open(OUTPUT_DIR / "frontend.json", "w", encoding="utf-8") as f:
        json.dump({"routes": frontend}, f, indent=2)
        
    with open(OUTPUT_DIR / "architecture.json", "w", encoding="utf-8") as f:
        json.dump({"modules": [{"name": "NLP", "status": "Active"}, {"name": "Risk", "status": "Completed"}]}, f, indent=2)
        
    with open(OUTPUT_DIR / "workflow.json", "w", encoding="utf-8") as f:
        json.dump({"states": ["Intake Pending", "NLP Running", "Risk Calculated"]}, f, indent=2)
        
    with open(OUTPUT_DIR / "pipeline.json", "w", encoding="utf-8") as f:
        json.dump({"timings": []}, f, indent=2)
        
    with open(OUTPUT_DIR / "backend.json", "w", encoding="utf-8") as f:
        json.dump({"services": []}, f, indent=2)
        
    with open(OUTPUT_DIR / "dependency.json", "w", encoding="utf-8") as f:
        json.dump({"dependencies": []}, f, indent=2)

    print(f"Extraction complete. 8 JSON files written to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
