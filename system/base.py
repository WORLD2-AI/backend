import sys
import os

root_path = os.getenv("ROOT_PATH")
if root_path is None:
    root_path = os.path.dirname(os.path.abspath(__file__))
    os.environ["ROOT_PATH"] = root_path
sys.path.append(root_path)


openai_api_key = ["sk-ded95fe2fbac46d8995610ee473095ed"]
from utils.utils import *