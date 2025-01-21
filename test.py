"""


File: gpt_structure.py
Description: Wrapper functions for calling OpenAI APIs.


"""
import json
import os
import random
import openai
import time

# from dotenv import load_dotenv, find_dotenv
# from litellm import completion
# from gpt4all import GPT4All, Embed4All

# from reverie.backend_server.persona.prompt_template.gpt_structure import temp_sleep
# from reverie.backend_server.utils import *

# openai.api_key = random.choice(openai_api_key)
# os.environ["http_proxy"] = "http://127.0.0.1:7899"
# os.environ["https_proxy"] = "https://127.0.0.1:7899"

# load_dotenv(override=True)
# load_dotenv(find_dotenv(), override=True)


# def ChatGPT_request(prompts: object) -> object:
#     """
#       Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
#       server and returns the response.
#       ARGS:
#         prompts: a str prompt
#         gpt_parameter: a python dictionary with the keys indicating the names of
#                        the parameter and the values indicating the parameter
#                        values.
#       RETURNS:
#         a str of GPT-3's response.
#       """
#     time.sleep(1)

#     try:
#         # openai call
#         completion = openai.ChatCompletion.create(
#             engine="text-davinci-003",
#             prompt=prompt
#         )

#         # llama2 call
#         # response = completion(model="meta-llama/Llama-2-7b-hf",
#         #                       messages=[{"role": "user", "content": prompts}])
#         # reply = response["choices"][0]["message"]["content"]

#         return reply
#     except Exception as e:
#         return f"ChatGPT ERROR:{e}"


# def ChatGPT_turbo_request(prompt: str, gpt_parameter={}) -> object:
#     """
#   Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
#   server and returns the response.
#   ARGS:
#     prompt: a str prompt
#     gpt_parameter: a python dictionary with the keys indicating the names of
#                    the parameter and the values indicating the parameter
#                    values.
#   RETURNS:
#     a str of GPT-3's response.
#   """
#     # temp_sleep()
#     openai.api_key = random.choice(openai_api_key)

#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-4o",
#             messages=[{"role": "user", "content": prompts}]
#         )

#         return completion["choices"][0]["message"]["content"]

#     except Exception as e:
#         print(f"ChatGPT ERROR{e}")
#         return f"ChatGPT ERROR{e}"


# def GPT4_request(prompt: str) -> object:
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
#     # temp_sleep()

#     try:
#         completion = openai.ChatCompletion.create(
#             model="gpt-4",
#             messages=[{"role": "user", "content": prompt}]
#         )
#         return completion["choices"][0]["message"]["content"]

#     except Exception as e:
#         print(f"ChatGPT ERROR: {e}")
#         return f"ChatGPT ERROR: {e}"


# def LLAMA_7b_request(prompts: object) -> object:
#     """
#       Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
#       server and returns the response.
#       ARGS:
#         prompts: a str prompt
#         gpt_parameter: a python dictionary with the keys indicating the names of
#                        the parameter and the values indicating the parameter
#                        values.
#       RETURNS:
#         a str of GPT-3's response.
#       """
#     time.sleep(1)

#     try:
#         # llama2 call
#         response = completion(model="meta-llama/Llama-2-7b-hf",
#                               messages=[{"role": "user", "content": prompts}])
#         reply = response["choices"][0]["message"]["content"]
#         return reply

#     except Exception as e:
#         print(f"ChatGPT ERROR: {e}")
#         return f"ChatGPT ERROR: {e}"


# def temp_sleep(seconds=0.1):
#     time.sleep(seconds)


# def GPTLocal_request(prompt, max_tokens=50) -> object:
#     """
#     Given a prompt, make a request to GPT4All model and returns the response.
#     ARGS:
#       prompt: a str prompt
#       gpt_parameter: a python dictionary with the keys indicating the names of
#                      the parameter and the values indicating the parameter
#                      values.
#     RETURNS:
#       a str of GPT4All's response.
#       :param max_tokens: int
#     """
#     temp_sleep()
#     model = GPT4All(gpt4all_model)
#     # # anthropic
#     # response = completion(model="claude-2", messages=messages)
#     try:
#         output = model.generate(prompt, max_tokens=max_tokens)
#         return output

#     except Exception as e:
#         print(f"ChatGPT ERROR: {e}")
#         return f"ChatGPT ERROR: {e}"



def test():
    print(", ".join("the Ville:artist's co-living space: kitchen:<random>".replace(": ",":").split(":")[:-1]))


if __name__ == "__main__":
    test()
