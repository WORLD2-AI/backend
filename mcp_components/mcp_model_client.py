# mcp_components/mcp_model_client.py
import openai
import os
import logging
import time
import traceback
from typing import Optional
import requests
import urllib3

from mcp_components.common_mcp_types import LLMRequest, LLMResponse, DialogMessage

logger = logging.getLogger(__name__)

class ModelClient:
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 api_base_url: Optional[str] = None):
        # 添加DeepSeek专用配置
        self.api_key = api_key or "sk-98f0451cbb1f4f75802c35923f5b0d2f"  # 直接设置API密钥
        self.api_base_url = api_base_url or "https://api.deepseek.com/v1"
        
        # 强制设置openai库配置
        openai.api_key = self.api_key
        openai.api_base = self.api_base_url
        
        # 完全禁用代理设置
        os.environ['no_proxy'] = '*'
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''
        os.environ['all_proxy'] = ''
        
        # 禁用SSL警告
        urllib3.disable_warnings()
        
        # 配置requests
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.verify = False
        
        logger.info(f"ModelClient initialized. OpenAI API Key {'SET' if openai.api_key else 'NOT SET'}. API Base: {openai.api_base or 'Not Set (will use OpenAI default if not overridden)'}")

    def call_llm(self, request_data: LLMRequest, max_retries: int = 3, retry_delay_seconds: int = 5) -> Optional[LLMResponse]:
        # Prioritize instance-specific API key and base, then globally set openai lib values, then defaults.
        effective_api_key = self.api_key or openai.api_key
        effective_api_base = self.api_base_url or openai.api_base or "https://api.deepseek.com/v1" # Ensure a base is always there

        if not effective_api_key:
            logger.error("API key for LLM is not effectively set. Cannot make API call.")
            return None
        
        # Store original openai settings to restore them after the call if they were changed
        original_openai_key = openai.api_key
        original_openai_base = openai.api_base

        # Set for this specific call context
        openai.api_key = effective_api_key
        openai.api_base = effective_api_base

        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting LLM API call (Attempt {attempt + 1}/{max_retries}) to {openai.api_base} with model {request_data.parameters.model_name}")
                
                messages_for_api = [msg.model_dump() for msg in request_data.messages]

                # 使用预配置的session
                openai.api_requestor.APIRequestor._session = self.session
                
                response = openai.ChatCompletion.create(
                    model=request_data.parameters.model_name,
                    messages=messages_for_api,
                    temperature=request_data.parameters.temperature,
                    max_tokens=request_data.parameters.max_tokens,
                    # timeout=60 # Optional: API call timeout in seconds
                )
                
                raw_content = response.choices[0].message.content.strip()
                logger.info(f"LLM API call successful. Raw response length: {len(raw_content)}")
                
                return LLMResponse(raw_content=raw_content, processed_content=raw_content)

            except openai.error.RateLimitError as e:
                last_error = e
                logger.warning(f"Rate limit exceeded (Attempt {attempt + 1}/{max_retries}): {e}. Retrying after delay...")
            except openai.error.APIConnectionError as e:
                last_error = e
                logger.error(f"API Connection Error (Attempt {attempt + 1}/{max_retries}): {e}")
            except openai.error.InvalidRequestError as e:
                last_error = e
                logger.error(f"Invalid Request Error (Attempt {attempt + 1}/{max_retries}): {e}")
                break # No point retrying clearly invalid requests
            except openai.error.AuthenticationError as e:
                last_error = e
                logger.error(f"Authentication Error: {e}. Please check your API key ({openai.api_key[:5]}...{openai.api_key[-4:] if openai.api_key else 'None'}).")
                break # No point retrying authentication errors
            except openai.error.APIError as e: # Catch other OpenAI API errors
                last_error = e
                logger.error(f"OpenAI API Error (Attempt {attempt + 1}/{max_retries}): {e}")
            except Exception as e: # Catch any other unexpected exceptions
                last_error = e
                logger.error(f"An unexpected error occurred during LLM call (Attempt {attempt + 1}/{max_retries}): {str(e)}")
                logger.error(traceback.format_exc())
            
            if attempt < max_retries - 1:
                current_retry_delay = retry_delay_seconds * (2 ** attempt) # Exponential backoff
                logger.info(f"Waiting {current_retry_delay} seconds before retrying...")
                time.sleep(current_retry_delay)
            else:
                logger.error(f"LLM API call failed after {max_retries} attempts.")
        
        # Restore original openai library settings
        openai.api_key = original_openai_key
        openai.api_base = original_openai_base
        
        if last_error:
            logger.error(f"Final error after all retries: {last_error}")
        return None