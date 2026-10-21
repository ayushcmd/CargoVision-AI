import os
import sys
import uvicorn

if __name__ == "__main__":
    # Ensure current working directory and module paths are set to full model/src/api
    project_root = os.path.abspath(os.path.dirname(__file__))
    api_dir = os.path.join(project_root, "full model", "src", "api")
    
    # Add project paths to sys.path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    if api_dir not in sys.path:
        sys.path.insert(0, api_dir)
        
    os.chdir(api_dir)
    
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "7860"))
    
    print(f"[CargoVision AI] Starting API on {host}:{port} from {api_dir}...")
    uvicorn.run("main:app", host=host, port=port)
