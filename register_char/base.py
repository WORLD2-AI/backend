import sys
import os

root_path = os.getenv("ROOT_PATH")
if root_path is None:
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.environ["ROOT_PATH"] = root_path
sys.path.append(root_path)



