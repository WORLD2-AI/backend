import sys
import os

root_path = os.getenv("ROOT_PATH")
if root_path is None:
    root_path = os.path.dirname(os.path.abspath(__file__))
    os.environ["ROOT_PATH"] = root_path
sys.path.append(root_path)


openai_api_key = ["sk-6ee322061b414adf834e1733153cb9ae"]
from utils.utils import *