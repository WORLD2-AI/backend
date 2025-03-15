# Copy and paste your OpenAI API Key
import json
import re
import logging
import traceback

# Put your name
key_owner = "test_sim_ai"

maze_assets_loc = "F:\\town\\environment\\frontend_server\\static_dirs\\assets"
env_matrix = f"{maze_assets_loc}/the_ville/matrix2"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"

fs_storage = "F:\\town\\environment\\frontend_server\\storage"
fs_temp_storage = "F:\\town\\environment\\frontend_server\\temp_storage"
fs_back_end = "F:\\town\\reverie\\backend_server"
collision_block_id = "32125"
emb_url = "http://127.0.0.1:11434"
api_url = "http://127.0.0.1"
openai_api_key = ["app-jLfekcAowJX712HNmWYrclpA"]

# api_url = "http://8.130.125.153"
# openai_api_key = ["app-cYXRNIAFUZY7ywce7OOkXcN9"]
# Verbose 
debug = True
logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
logger = logging.getLogger()

def logger_info(*args):
    """
    Recursively print JSON data with indentation for better readability.
    
    :param args: The data to print.
    """
    stack = traceback.extract_stack()
    previous_frame = stack[-2]
    previous_function = previous_frame.name
    previous_file = previous_frame.filename
    previous_line_number = previous_frame.lineno
    logger.info(f"Call stack function [{previous_function}]: line :[{previous_file}:{previous_line_number}]")
    for arg in args:
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
