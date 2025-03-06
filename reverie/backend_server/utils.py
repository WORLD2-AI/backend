# Copy and paste your OpenAI API Key
import json
import re
import logging
import sys
import time
import traceback

# Put your name
key_owner = "test_sim_ai"

maze_assets_loc = "F:\\town\\environment\\frontend_server\\static_dirs\\assets"
env_matrix = f"{maze_assets_loc}/the_ville/matrix2"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"

fs_storage = "F:\\town\\environment\\frontend_server\\storage"
fs_temp_storage = "F:\\town\\environment\\frontend_server\\temp_storage"
fs_back_end = "F:\\town\\reverie\\backend_server"
collision_block_id = "0"
emb_url = "http://127.0.0.1:11434"
# api_url = "http://127.0.0.1"
openai_api_key = ["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"]

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

if __name__ == '__main__':
    curr_gpt_response = filter_result('```json\n{"output": 8}\n```')
    print(curr_gpt_response)
    ret = json.loads(curr_gpt_response)
    print(ret["output"])
