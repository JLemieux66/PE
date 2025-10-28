"""
Fix imports after reorganization
Updates import statements to reflect new file locations
"""
import re
from pathlib import Path

BASE_DIR = Path(r"c:\Users\josep\documentation-helper")

# Import mappings (old import -> new import)
IMPORT_FIXES = {
    "from src.models.database_models import": "from src.models.database_models import",
    "import src.models.database_models as database_models": "import src.models.database_models as database_models",
    "from src.enrichment.crunchbase_helpers import": "from src.enrichment.crunchbase_helpers import",
    "import src.enrichment.crunchbase_helpers as crunchbase_helpers": "import src.enrichment.crunchbase_helpers as crunchbase_helpers",
    "from src.utils.logger import": "from src.utils.logger import",
    "import src.utils.logger as logger": "import src.utils.logger as logger",
    "from src.utils.consts import": "from src.utils.consts import",
    "import src.utils.consts as consts": "import src.utils.consts as consts",
    "from src.config.pe_firms_config import": "from src.config.pe_firms_config import",
    "import src.config.pe_firms_config as pe_firms_config": "import src.config.pe_firms_config as pe_firms_config",
}

def fix_imports_in_file(file_path):
    """Fix imports in a single file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Apply all import fixes
        for old_import, new_import in IMPORT_FIXES.items():
            content = content.replace(old_import, new_import)
        
        # Only write if changed
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"   ❌ Error in {file_path.name}: {e}")
        return False

def fix_all_imports():
    """Fix imports in all Python files"""
    print("=" * 80)
    print("FIXING IMPORTS")
    print("=" * 80)
    
    # Directories to scan for Python files
    scan_dirs = [
        BASE_DIR / "src",
        BASE_DIR / "scripts",
        BASE_DIR / "frontend",
        BASE_DIR,  # Root files like api.py, main.py
    ]
    
    fixed_count = 0
    scanned_count = 0
    
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
            
        # Find all Python files recursively
        for py_file in scan_dir.rglob("*.py"):
            # Skip __pycache__ and .venv
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue
            
            scanned_count += 1
            if fix_imports_in_file(py_file):
                fixed_count += 1
                print(f"   ✅ Fixed: {py_file.relative_to(BASE_DIR)}")
    
    print("\n" + "=" * 80)
    print("IMPORT FIXING COMPLETE!")
    print("=" * 80)
    print(f"✅ Files scanned: {scanned_count}")
    print(f"✅ Files updated: {fixed_count}")
    print("=" * 80)

if __name__ == "__main__":
    fix_all_imports()
