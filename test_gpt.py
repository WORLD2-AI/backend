import requests
import json
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API配置
API_KEY = "sk-6ee322061b414adf834e1733153cb9ae"
API_URL = "https://api.deepseek.com/v1/chat/completions"  # 更换为deepseek的API端点

# 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 请求数据
data = {
    "model": "deepseek-chat",  # 更换模型
    "messages": [
        {
            "role": "user",
            "content": """Generate activity data for an hour from 08:00 AM to the following hour. 
Important: per activity duration must between 3 and 5 minutes and total duration must add up to 1 hour. 
Output only include json array data and nothing else. 
json data key include: activity,time,duration,action. 
like {"time": "14:00" ,"duration": "4", "action": "do something"}. 
"time" is 24 hours, no am and pm."""
        }
    ],
    "temperature": 1,
    "max_tokens": 7000
}

# 代理设置
proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}

# 发送请求
try:
    response = requests.post(
        API_URL, 
        headers=headers, 
        json=data, 
        verify=False,
        proxies=proxies,
        timeout=30
    )
    response.raise_for_status()  # 检查响应状态
    result = response.json()
    print("Response:", result['choices'][0]['message']['content'])
except requests.exceptions.RequestException as e:
    print(f"Error occurred: {e}")
    if hasattr(e.response, 'text'):
        print(f"Response text: {e.response.text}") 