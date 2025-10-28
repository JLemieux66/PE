"""
Add path setup to all scripts
"""
from pathlib import Path

BASE_DIR = Path(r"c:\Users\josep\documentation-helper")

PATH_SETUP = """import sys
from pathlib import Path
# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

"""

SCRIPTS_SETUP_2_LEVELS = """import sys
from pathlib import Path
# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

"""

def add_path_setup(file_path, levels_up=3):
    """Add path setup to beginning of file if not present"""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Skip if already has path setup
        if "sys.path.insert" in content:
            return False
        
        # Skip if doesn't import from src
        if "from src." not in content and "import src." not in content:
            return False
        
        # Find where to insert (after docstring if present)
        lines = content.split('\n')
        insert_pos = 0
        
        # Skip shebang
        if lines and lines[0].startswith('#!'):
            insert_pos = 1
        
        # Skip docstring
        if insert_pos < len(lines) and lines[insert_pos].strip().startswith('"""'):
            # Multi-line docstring
            for i in range(insert_pos + 1, len(lines)):
                if '"""' in lines[i]:
                    insert_pos = i + 1
                    break
        
        # Insert path setup
        setup = PATH_SETUP if levels_up == 3 else SCRIPTS_SETUP_2_LEVELS
        lines.insert(insert_pos, setup)
        
        new_content = '\n'.join(lines)
        file_path.write_text(new_content, encoding='utf-8')
        return True
        
    except Exception as e:
        print(f"   ❌ Error in {file_path.name}: {e}")
        return False

def add_path_setup_to_all():
    """Add path setup to all scripts"""
    print("=" * 80)
    print("ADDING PATH SETUP TO SCRIPTS")
    print("=" * 80)
    
    directories = {
        BASE_DIR / "scripts": 3,  # 3 levels up (scripts/analysis/file.py → root)
        BASE_DIR / "frontend": 2,  # 2 levels up (frontend/file.py → root)
    }
    
    updated_count = 0
    
    for directory, levels in directories.items():
        if not directory.exists():
            continue
        
        print(f"\n📁 {directory.relative_to(BASE_DIR)}")
        print("-" * 80)
        
        for py_file in directory.rglob("*.py"):
            if "__pycache__" in str(py_file) or "__init__" in py_file.name:
                continue
            
            if add_path_setup(py_file, levels):
                updated_count += 1
                print(f"   ✅ {py_file.relative_to(BASE_DIR)}")
    
    print("\n" + "=" * 80)
    print(f"✅ Files updated: {updated_count}")
    print("=" * 80)

if __name__ == "__main__":
    add_path_setup_to_all()
