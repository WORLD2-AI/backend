# Copy and paste your OpenAI API Key
import json
import re
import logging
import sys
import time
import traceback

TWITTER_API_KEY = 'xAsAN0Sodd7sN8MjGjkFQDAWU'
TWITTER_API_SECRET_KEY = '2mhTD5tc0zfxqCHKVVQitBJjbaT0YVqfEQjie9Nez67P3TsmIS'


# Put your name
key_owner = "test_sim_ai"

maze_assets_loc = "D:\\aitown\\environment\\frontend_server\\static_dirs\\assets"
env_matrix = f"{maze_assets_loc}/the_ville/matrix2"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"

fs_storage = "D:\\aitown\\environment\\frontend_server\\storage"
fs_temp_storage = "D:\\aitown\\environment\\frontend_server\\temp_storage"
fs_back_end = "D:\\aitown\\reverie\\backend_server"

emb_url = "http://127.0.0.1:11434"
# api_url = "http://127.0.0.1"
openai_api_key = ["sk-058aed3cf0b942068740c516fef37c51"]

# api_url = "http://8.130.125.153"
# openai_api_key = ["app-cYXRNIAFUZY7ywce7OOkXcN9"]
# Verbose 
debug = True
logging.basicConfig(level=logging.DEBUG if debug else logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',stream= sys.stdout)
logger = logging.getLogger()
print_call_stack = False
log_file_path = "backend_server.log"
file =  open(log_file_path, "a") 
def logger_info(*args):
    """
    Recursively print JSON data with indentation for better readability.
    
    :param args: The data to print.
    """
    stack = traceback.extract_stack()
    last_stck = stack[-2:-1]
    if print_call_stack:
        logger.info("---------------call stack------------")
        last_stck = stack[-5:-1]
    str_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    for frame in last_stck:
        # put log info to file
        
        file.write(f"Function [{frame.name}]: File {frame.filename}, line {frame.lineno}\n")
        logger.info(f"{str_time} Function [{frame.name}]: File {frame.filename}, line {frame.lineno}")
    for arg in args:
        file.write(str(arg))
        file.write("\n")
        logger.info(arg)
        
def filter_result(respone:str):
    respone = respone.strip()
    if respone is None:
        return ""
    if "</think>" in respone:
        respone = respone.split("</think>")[1]
    if "**" in respone:
        respone = respone.replace("**","")
    if respone.startswith("```"):
        json_pattern =  r'```json([\s\S]+)```'
        match = re.search(json_pattern,respone)
        if match is not None:
            respone =  match.group(1)
    respone = respone.strip()
    return respone

def validate_json(json_str):
    """
    Validate if the given string is a valid JSON.
    
    :param json_str: The string to validate.
    :return: True if valid JSON, False otherwise.
    """
    try:
        json_str = json_str.strip()
        json.loads(json_str)
        return True
    except ValueError:
        return False
    
# if __name__ == '__main__':
#     curr_gpt_response = filter_result('```json\n{"output": 8}\n```')
#     print(curr_gpt_response)
#     ret = json.loads(curr_gpt_response)
#     print(ret["output"])


def recursive_parse(obj):
    if isinstance(obj, str):
        try:
            parsed = json.loads(obj)
            return recursive_parse(parsed)
        except (json.JSONDecodeError, TypeError):
            return obj
    elif isinstance(obj, dict):
        return {k: recursive_parse(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [recursive_parse(item) for item in obj]
    else:
        return obj

if  __name__ == "__main__":
    json_str = "{\"id\": 5, \"name\": \"chen kiki\", \"user_id\": 5, \"first_name\": \"kiki\", \"last_name\": \"chen\", \"age\": 25, \"sex\": \"female\", \"innate\": \"friendly, helpful, cryptocurrency investor\", \"learned\": \"kiki is a single man who loves making friends. she is always looking for new ways to improve himself and become an outstanding investor\", \"currently\": \"kiki is neighbors with his friend cichengege. kiki is a cryptocurrency investor and also holds some positions in the small town\", \"lifestyle\": \"kiki usually goes to bed around 11 pm., wakes up at 9 am., and has dinner around 6 pm. He enjoys entertainment\", \"wake_time\": 7, \"sleep_time\": 22, \"status\": \"PENDING\", \"created_at\": \"2025-05-01 09:51:11\", \"updated_at\": \"2025-05-01 09:51:11\", \"position\": [0, 0], \"start_minute\": 1001, \"duration\": 4, \"action\": \"Reflect on personal growth\", \"emoji\": \"\\ud83e\\ude9e\\ud83c\\udf31\", \"path\": [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0], [5, 0], [6, 0], [7, 0], [8, 0], [9, 0], [10, 0], [11, 0], [12, 0], [13, 0], [14, 0], [14, 1], [14, 2], [14, 3], [14, 4], [14, 5], [14, 6], [14, 7], [14, 8], [14, 9], [14, 10], [14, 11], [14, 12], [14, 13], [14, 14], [14, 15], [14, 16], [14, 17], [14, 18], [14, 19], [14, 20], [14, 21], [14, 22], [14, 23], [14, 24], [14, 25], [14, 26], [14, 27], [14, 28], [15, 28], [16, 28], [17, 28], [18, 28], [19, 28], [20, 28], [21, 28], [22, 28], [23, 28], [24, 28], [25, 28], [26, 28], [27, 28], [28, 28], [29, 28], [30, 28], [31, 28], [32, 28], [33, 28], [34, 28], [35, 28], [35, 29], [35, 30], [36, 30], [37, 30], [38, 30], [39, 30], [40, 30], [40, 31], [40, 32], [40, 33], [40, 34], [40, 35], [40, 36], [40, 37], [40, 38], [40, 39], [40, 40], [40, 41], [40, 42], [40, 43], [40, 44], [40, 45], [40, 46], [40, 47], [40, 48], [40, 49], [40, 50], [40, 51], [40, 52], [40, 53], [40, 54], [39, 54], [39, 55], [39, 56], [38, 56], [37, 56], [36, 56], [35, 56], [34, 56], [33, 56], [32, 56], [31, 56], [30, 56], [29, 56], [28, 56], [27, 56], [26, 56], [26, 57], [26, 58], [26, 59], [26, 60], [26, 61], [26, 62], [26, 63], [26, 64], [26, 65], [26, 66], [26, 67], [26, 68], [26, 69], [26, 70], [26, 71], [26, 72], [25, 72], [24, 72], [23, 72], [22, 72], [22, 73], [22, 74], [22, 75], [22, 76], [21, 76], [21, 77], [20, 77], [20, 78], [20, 79], [20, 80], [20, 81], [20, 82], [20, 83], [20, 84], [20, 85], [20, 86], [20, 87], [20, 88], [20, 89], [21, 89], [22, 89], [23, 89], [24, 89]], \"site\": \"the ville:johnson park:lake:log bridge\"}"
    print(recursive_parse(json_str))