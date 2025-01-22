# Copy and paste your OpenAI API Key
import json
from collections.abc import Iterable
openai_api_key = [
   
]
# Put your name
key_owner = "test_sim_ai"

maze_assets_loc = "E:\\code\\python\\Town\\environment\\frontend_server\\static_dirs\\assets"
env_matrix = f"{maze_assets_loc}/the_ville/matrix"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"

fs_storage = "E:\\code\\python\\Town\\environment\\frontend_server\\storage"
fs_temp_storage = "E:\\code\\python\\Town\\environment\\frontend_server\\temp_storage"
fs_back_end = "E:\\code\python\\Town\\reverie\\backend_server"
collision_block_id = "32125"
# api_url = "http://127.0.0.1:11434"
emb_url = "http://127.0.0.1:11434"
api_url = "http://127.0.0.1"
# Verbose 
debug = True

def print_json(data, indent=0):
    """
    Recursively print JSON data with indentation for better readability.
    
    :param data: The JSON data to print.
    :param indent: The current indentation level (used for recursive calls).
    """
    if data is None or  not data:
        print("None")
        return
    # If the data is a dictionary, iterate over its key-value pairs
    if isinstance(data, dict):
        print(' ' * indent + '{')
        for key, value in data.items():
            print(' ' * (indent + 4) + f'"{key}": ', end='')
            print_json(value, indent + 4)
        print(' ' * indent + '}')
    
    # If the data is a list, iterate over its elements
    elif isinstance(data, list):
        print(' ' * indent + '[')
        for item in data:
            print_json(item, indent + 4)
        print(' ' * indent + ']')
    elif isinstance(data, Iterable):
        print(' ' * indent ,json.dumps(data))
        
    # If the data is a string, number, or boolean, print it directly
    else:
        print(' ' * indent ,'"',data,'"')