# openssl_helper.py
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.openai.com/v1",
    #如果需要代理，这里配置，比如：
    http_client={
        "proxies": {
            "http://": "http://192.168.238.1:7890",
            "https://": "http://192.168.238.1:7890"
        }
    }
)

def generate_openssl_code(prompt: str, model="gpt-4"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": f"请用 OpenSSL 编写如下功能的加密代码，并包含注释：{prompt}"}
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content
