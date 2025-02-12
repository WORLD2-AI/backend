"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: gpt_structure.py
Description: Wrapper functions for calling OpenAI APIs.
"""
import json
import random
import openai
import time
import re
from utils import *

openai.api_key = random.choice(openai_api_key)


def temp_sleep(seconds=0.1):
    time.sleep(seconds)


def ChatGPT_single_request(prompt):
    temp_sleep()
    openai.api_key = random.choice(openai_api_key)

    completion = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion["choices"][0]["message"]["content"]


# ============================================================================
# #####################[SECTION 1: CHATGPT-4o STRUCTURE] ######################
# ============================================================================

def GPT4_request(prompt):
    """
  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
  server and returns the response. 
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with the keys indicating the names of  
                   the parameter and the values indicating the parameter 
                   values.   
  RETURNS: 
    a str of GPT-4o's response. 
  """
    temp_sleep()

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion["choices"][0]["message"]["content"]

    except Exception as e:
        logger_info("ChatGPT ERROR",e)
        return "ChatGPT ERROR"


def ChatGPT_request(prompt, gpt_parameter={}):
    """
  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
  server and returns the response. 
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with the keys indicating the names of  
                   the parameter and the values indicating the parameter 
                   values.   
  RETURNS: 
    a str of GPT-4o's response. 
  """
    # temp_sleep()
    openai.api_key = random.choice(openai_api_key)
    logger_info("-----------prompt-------------------",prompt)
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        result =  completion["choices"][0]["message"]["content"]
        logger_info("-----------result-------------------",result)
        return filter_result(respone=result)

    except Exception as e:
        logger_info(f"ChatGPT ERROR{e}")
        return f"ChatGPT ERROR{e}"


def GPT4_safe_generate_response(prompt,
                                example_output,
                                special_instruction,
                                repeat=3,
                                fail_safe_response="error",
                                func_validate=None,
                                func_clean_up=None,
                                verbose=False):
    prompt = 'GPT-4o Prompt:\n"""\n' + prompt + '\n"""\n'
    prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
    prompt += "Example output json:\n"
    prompt += '{"output": "' + str(example_output) + '"}'

    if verbose:
        logger_info("CHAT GPT PROMPT")
        logger_info(prompt)

    for i in range(repeat):

        try:
            curr_gpt_response = GPT4_request(prompt).strip()
            end_index = curr_gpt_response.rfind('}') + 1
            curr_gpt_response = curr_gpt_response[:end_index]
            curr_gpt_response = json.loads(curr_gpt_response)["output"]

            if func_validate(curr_gpt_response, prompt=prompt):
                return func_clean_up(curr_gpt_response, prompt=prompt)

            if verbose:
                logger_info("---- repeat count: \n", i, curr_gpt_response)
                logger_info(curr_gpt_response)
                logger_info("~~~~")

        except:
            pass

    return False


def ChatGPT_safe_generate_response(prompt,
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False):
    # prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
    openai.api_key = random.choice(openai_api_key)

    prompt = '"""\n' + prompt + '\n"""\n'
    prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
    prompt += "Example output json:\n"
    prompt += '{"output": "' + str(example_output) + '"}'


    for i in range(repeat):
        try:
            curr_gpt_response = ChatGPT_request(prompt)
            end_index = curr_gpt_response.rfind('}') + 1
            curr_gpt_response = curr_gpt_response[:end_index]
            curr_gpt_response = json.loads(curr_gpt_response)["output"]

            if func_validate(curr_gpt_response, prompt=prompt):
                return func_clean_up(curr_gpt_response, prompt=prompt)
            time.sleep(1)

        except:
            pass

    return False


def ChatGPT_safe_generate_response_OLD(prompt,
                                       repeat=3,
                                       fail_safe_response="error",
                                       func_validate=None,
                                       func_clean_up=None,
                                       verbose=False):

    openai.api_key = random.choice(openai_api_key)

    for i in range(repeat):
        try:
            curr_gpt_response = ChatGPT_request(prompt).strip()
            if func_validate(curr_gpt_response, prompt=prompt):
                return func_clean_up(curr_gpt_response, prompt=prompt)
        except Exception as e:
            logger_info("ChatGPT ERROR",e)
            pass
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
    temp_sleep()
    openai.api_key = random.choice(openai_api_key)
    # openai.api_key = random.choice(openai_api_key)
    print("-------------------request prompt---------------------")
    logger_info(prompt)
    try:
        response = openai.ChatCompletion.create(
            model=gpt_parameter["engine"],
            messages=[{"role": "user", "content": prompt}],
            temperature=gpt_parameter["temperature"],
            max_tokens=gpt_parameter["max_tokens"],
            top_p=gpt_parameter["top_p"],
            frequency_penalty=gpt_parameter["frequency_penalty"],
            presence_penalty=gpt_parameter["presence_penalty"],
            stream=gpt_parameter["stream"],
            stop=gpt_parameter["stop"], )
        time.sleep(1)
        print("---------------success result ---------------------------------")
        logger_info(response.choices[0]['message'], {})
        return response.choices[0]['message']['content']
    except Exception as e:
        print("-------------error result ----------------------------")
        logger_info(response,e)
        raise e


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
        time.sleep(1)
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
    # if verbose:
    openai.api_key = random.choice(openai_api_key)

    for i in range(repeat):
        try:
            curr_gpt_response = GPT_request(prompt, gpt_parameter).strip()
            if func_validate(curr_gpt_response, prompt=prompt):
                return func_clean_up(curr_gpt_response, prompt=prompt)
        except:
            pass
    return fail_safe_response


def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    if not text:
        text = "this is blank"
    openai.api_key = random.choice(openai_api_key)
    respone =  openai.Embedding.create(
        input=text, model=model)
    # logger_info(respone)
    return respone["data"][0]["embedding"]


if __name__ == '__main__':
    logger_info(filter_result('```json\n{"output": "🤔"}```'))


#     def __func_validate(gpt_response):
#         if len(gpt_response.strip()) <= 1:
#             return False
#         if len(gpt_response.strip().split(" ")) > 1:
#             return False
#         return True


#     def __func_clean_up(gpt_response):
#         cleaned_response = gpt_response.strip()
#         return cleaned_response


#     output = safe_generate_response(prompt,
#                                     gpt_parameter,
#                                     5,
#                                     "rest",
#                                     __func_validate,
#                                     __func_clean_up,
#                                     True)

#     logger_info(output)
