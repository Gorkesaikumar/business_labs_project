import sys
from pathlib import Path

task3_dir = str(Path(__file__).parent.parent)
if task3_dir not in sys.path:
    sys.path.insert(0, task3_dir)
