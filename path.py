from pathlib import Path
import sys
from util.helpers import load_markdown_for_prompt
print("Starting....")
file= "flask_CLAUDE.md"
print(f"Loading markdown file: {file}")
test_path = load_markdown_for_prompt(file)
project_root = Path(__file__).parent
#path = sys.path.insert(0, str(project_root))
#print(f"Project root added to sys.path: {path}")
print(f"Project root added to sys.path: {project_root}")
print(f"Loaded markdown content preview: {test_path}")