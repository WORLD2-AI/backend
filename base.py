import sys
import os

root_path = os.getenv("ROOT_PATH")
if root_path is None:
    root_path = os.path.dirname(os.path.abspath(__file__))
    os.environ["ROOT_PATH"] = root_path
sys.path.append(root_path)

# Twitter API配置
TWITTER_API_KEY = "your_twitter_api_key"
TWITTER_API_SECRET_KEY = "your_twitter_api_secret_key"



