import os
import sys
import importlib.util
from typing import List, Dict
import time

def get_script_path(script_name: str) -> str:
    """Get the full path of a script based on its name"""
    script_dirs = {
        'delete_index.py': 'src/elasticsearch',
        'create_index_prof.py': 'src/elasticsearch',
        'create_index_data.py': 'src/elasticsearch',
        'bulk_index_prof.py': 'src/elasticsearch',
        'bulk_index_data.py': 'src/elasticsearch',
        'pagerank_pipeline.py': 'src/pagerank',
        'create_index_p.py': 'src/pagerank',
        'bulk_index_p.py': 'src/pagerank'
    }
    
    if script_name in script_dirs:
        return os.path.join(script_dirs[script_name], script_name)
    return None

def load_module(file_path: str) -> Dict:
    """Load a Python module from file path"""
    try:
        parent_dir = os.path.dirname(os.path.dirname(file_path))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
            
        spec = importlib.util.spec_from_file_location("module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return {
            'path': file_path,
            'module': module,
            'name': os.path.basename(file_path)
        }
    except Exception as e:
        print(f"Error: {file_path} - {str(e)}")
        return None

def main():
    script_order = [
        'delete_index.py',
        'create_index_prof.py',
        'create_index_data.py',
        'create_index_p.py',
        'pagerank_pipeline.py',
        'bulk_index_prof.py',
        'bulk_index_data.py',
        'bulk_index_p.py'
    ]
    
    print("\n=== ES Init ===")
    
    modules = {}
    for script_name in script_order:
        file_path = get_script_path(script_name)
        if file_path and os.path.exists(file_path):
            module = load_module(file_path)
            if module:
                modules[script_name] = module
        else:
            print(f"Error: {script_name} not found")
            return
    
    if not modules:
        print("Error: No modules found")
        return
    
    for script_name in script_order:
        if script_name in modules:
            print(f"\n> {script_name}")
            try:
                if hasattr(modules[script_name]['module'], 'main'):
                    modules[script_name]['module'].main()
                    print("✓ Done")
                else:
                    print(f"Error: {script_name} has no main()")
                    return
            except Exception as e:
                print(f"Error: {script_name} failed - {str(e)}")
                return
        
        time.sleep(1)
    
    print("\n=== Complete ===")

if __name__ == "__main__":
    main() 