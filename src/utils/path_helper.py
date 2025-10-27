"""
Add project root to path helper
"""
import sys
from pathlib import Path

# Get the project root (2 levels up from this file if in scripts/*)
def add_project_root_to_path():
    """Add the project root directory to sys.path"""
    # Get the current file's directory
    current_file = Path(__file__).resolve()
    
    # Determine project root based on file location
    if "scripts" in current_file.parts:
        # We're in scripts/* directory - go up to root
        project_root = current_file.parent.parent.parent
    elif "src" in current_file.parts:
        # We're in src/* directory - go up to root
        project_root = current_file.parent.parent
    else:
        # We're likely in the root already
        project_root = current_file.parent
    
    # Add to path if not already there
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    return project_root
