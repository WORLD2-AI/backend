
import json
import random
import openai
import time

import requests

from utils import *

openai.api_key = random.choice(openai_api_key)

# from litellm import completion


def temp_sleep(seconds=0.5):
    time.sleep(seconds)


def ChatGPT_single_request(prompt):
    return ChatGPT_request(prompt)


# ============================================================================
# #####################[SECTION 1: CHATGPT-3 STRUCTURE] ######################
# ============================================================================

# def GPT4_request(prompt):
#     """
#     Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
#     server and returns the response.
#     ARGS:
#       prompt: a str prompt
#       gpt_parameter: a python dictionary with the keys indicating the names of
#                      the parameter and the values indicating the parameter
#                      values.
#     RETURNS:
#       a str of GPT-3's response.
#     """
#     temp_sleep()

#     try:
#         completion = openai.ChatCompletion.create(
#             model="gpt-4",
#             messages=[{"role": "user", "content": prompt}]
#         )
#         return completion["choices"][0]["message"]["content"]

#     except:
#         print("ChatGPT ERROR")
#         return "ChatGPT ERROR"


def ChatGPT_request(prompt):
    """
    Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
    server and returns the response.
    ARGS:
      prompt: a str prompt
      gpt_parameter: a python dictionary with the keys indicating the names of
                     the parameter and the values indicating the parameter
                     values.
    RETURNS:
      a str of llm response.
    """
    temp_sleep()
    # openai.api_key = random.choice(openai_api_key)
    print("-------------------request prompt---------------------")
    logger_info(prompt)
    token =  random.choice(openai_api_key)
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization":"Bearer "+token
        }
        data = {
            "inputs": {"query": prompt},
            "response_mode": "blocking",
            "user":"test_user"
            # "messages":[{"role": "user", "content": prompt}],
            # "stream": False
        }
        url = f"{api_url}/v1/completion-messages"
        response = requests.post(url, headers=headers, data=json.dumps(data),timeout = 120)
        
        if response.status_code == 200:
            print("---------------success result ---------------------------------")
            logger_info(response.json().get("answer", {}))
            return filter_result(response.json().get("answer", {}))
        else:
            print("-------------error result ----------------------------")
            logger_info(response.json())
            response.raise_for_status()

    except Exception as e:
        print ("ChatGPT ERROR",e)
        return ""


# def GPT4_safe_generate_response(prompt,
#                                 example_output,
#                                 special_instruction,
#                                 repeat=3,
#                                 fail_safe_response="error",
#                                 func_validate=None,
#                                 func_clean_up=None,
#                                 verbose=False):
#     prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
#     prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
#     prompt += "Example output json:\n"
#     prompt += '{"output": "' + str(example_output) + '"}'

#     if verbose:
#         print ("CHAT GPT PROMPT")
#         print (prompt)

#     for i in range(repeat):

#         try:
#             curr_gpt_response = GPT4_request(prompt).strip()
#             end_index = curr_gpt_response.rfind('}') + 1
#             curr_gpt_response = curr_gpt_response[:end_index]
#             curr_gpt_response = json.loads(curr_gpt_response)["output"]

#             if func_validate(curr_gpt_response, prompt=prompt):
#                 return func_clean_up(curr_gpt_response, prompt=prompt)

#             if verbose:
#                 print ("---- repeat count: \n", i, curr_gpt_response)
#                 print (curr_gpt_response)
#                 print ("~~~~")

#         except:
#             pass

#     return False


def ChatGPT_safe_generate_response(prompt,
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False):
    # prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
    # openai.api_key = random.choice(openai_api_key)

    prompt = '"""\n' + prompt + '\n"""\n'
    prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
    prompt += "Example output json:\n"
    prompt += '{"output": "' + str(example_output) + '"}'

    for i in range(repeat):

        try:
            curr_gpt_response = ChatGPT_request(prompt).strip()
            # end_index = curr_gpt_response.rfind('}') + 1
            # curr_gpt_response = curr_gpt_response[:end_index]
            res = json.loads(curr_gpt_response)
            curr_gpt_response = res["output"]

            # print ("---ashdfaf")
            # print (curr_gpt_response)
            # print ("000asdfhia")

            if func_validate(curr_gpt_response, prompt=prompt):
                return func_clean_up(curr_gpt_response, prompt=prompt)

        except:
            pass

    return False


def ChatGPT_safe_generate_response_OLD(prompt,
                                       repeat=3,
                                       fail_safe_response="error",
                                       func_validate=None,
                                       func_clean_up=None,
                                       verbose=False):
    if verbose:
        print ("CHAT GPT PROMPT")
        print (prompt)

    openai.api_key = random.choice(openai_api_key)

    for i in range(repeat):
        try:
            curr_gpt_response = ChatGPT_request(prompt).strip()
            if func_validate(curr_gpt_response, prompt=prompt):
                return func_clean_up(curr_gpt_response, prompt=prompt)
            if verbose:
                print (f"---- repeat count: {i}")
                print (curr_gpt_response)
                print ("~~~~")

        except:
            pass
    print ("FAIL SAFE TRIGGERED")
    return fail_safe_response


# ============================================================================
# ###################[SECTION 2: ORIGINAL GPT-3 STRUCTURE] ###################
# ============================================================================

def GPT_request(prompt, gpt_parameter):
    """
    Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
    server and returns the response.
    ARGS:
      prompt: a str prompt
      gpt_parameter: a python dictionary with the keys indicating the names of
                     the parameter and the values indicating the parameter
                     values.
    RETURNS:
      a str of GPT-3's response.
    """

    openai.api_key = random.choice(openai_api_key)
    return ChatGPT_request(prompt=prompt)
    # try:
    #     headers = {
    #         "Content-Type": "application/json",
    #         "Authorization": "Bearer app-YModVQ7H9WeGudJOsLnw3s2I",
    #     }
        
    #     data = {
    #         "messages":[{"role": "user", "content": prompt}],
    #         "options":{
    #             "temperature": gpt_parameter["temperature"],
    #             "top_p":gpt_parameter["top_p"],
    #             "frequency_penalty":gpt_parameter["frequency_penalty"],
    #             "presence_penalty":gpt_parameter["presence_penalty"],
    #         },
    #         "max_tokens": gpt_parameter["max_tokens"],
    #         "stream": gpt_parameter["stream"]
    #     }
        
    #     url = f"{api_url}/api/completion-messages"
    #     response = requests.post(url, headers=headers, json=data)
        
    #     if response.status_code == 200:
    #         print(response.json())
    #         return response.json().get("message", {}).get("content", "")
    # except Exception as e:
    #     print (f"TOKEN LIMIT EXCEEDED: {e}")
    #     return "TOKEN LIMIT EXCEEDED"


def generate_prompt(curr_input, prompt_lib_file):
    """
    Takes in the current input (e.g. comment that you want to classifiy) and
    the path to a prompt file. The prompt file contains the raw str prompt that
    will be used, which contains the following substr: !<INPUT>! -- this
    function replaces this substr with the actual curr_input to produce the
    final promopt that will be sent to the GPT3 server.
    ARGS:
      curr_input: the input we want to feed in (IF THERE ARE MORE THAN ONE
                  INPUT, THIS CAN BE A LIST.)
      prompt_lib_file: the path to the promopt file.
    RETURNS:
      a str prompt that will be sent to OpenAI's GPT server.
    """
    if type(curr_input) == type("string"):
        curr_input = [curr_input]
    curr_input = [str(i) for i in curr_input]

    f = open(prompt_lib_file, "r")
    prompt = f.read()
    f.close()
    for count, i in enumerate(curr_input):
        prompt = prompt.replace(f"!<INPUT {count}>!", i)
    if "<commentblockmarker>###</commentblockmarker>" in prompt:
        prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
    return prompt.strip()


def safe_generate_response(prompt,
                           gpt_parameter,
                           repeat=5,
                           fail_safe_response="error",
                           func_validate=None,
                           func_clean_up=None,
                           verbose=False):
    openai.api_key = random.choice(openai_api_key)

    for i in range(repeat):
        curr_gpt_response = GPT_request(prompt, gpt_parameter)
        if func_validate(curr_gpt_response, prompt=prompt):
            return func_clean_up(curr_gpt_response, prompt=prompt)
    return fail_safe_response


def get_embedding(text, model="nomic-embed-text"):
    if text == "" :
        return []
    # use local embedding model
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "nomic-embed-text",
        "input": text
    }
    url = f"{emb_url}/api/embed"
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        content  = response.json()
        logger_info(content)
        return content.get("embeddings", [[]])[0]
    else:
        response.raise_for_status()



if __name__ == '__main__':
    gpt_parameter = {"engine": "gpt-4o", "max_tokens": 50,
                     "temperature": 0, "top_p": 1, "stream": False,
                     "frequency_penalty": 0, "presence_penalty": 0,
                     "stop": ['"']}
    curr_input = ["driving to a friend's house"]
    prompt_lib_file = "prompt_template/test_prompt_July5.txt"
    prompt = generate_prompt(curr_input, prompt_lib_file)

    def __func_validate(gpt_response):
        if len(gpt_response.strip()) <= 1:
            return False
        if len(gpt_response.strip().split(" ")) > 1:
            return False
        return True
    def __func_clean_up(gpt_response):
        cleaned_response = gpt_response.strip()
        return cleaned_response

    output = safe_generate_response(prompt,
                                    gpt_parameter,
                                    5,
                                    "rest",
                                    __func_validate,
                                    __func_clean_up,
                                    True)

    print (output)
