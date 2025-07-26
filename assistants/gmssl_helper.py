# gmssl_helper.py
import os
import httpx
from openai import OpenAI

# 代理地址
proxy = "http://192.168.238.1:7890"

# 创建带代理的 httpx.Client 实例
http_client = httpx.Client(proxies={
    "http://": proxy,
    "https://": proxy
})

# 初始化 OpenAI 客户端，传入 api_key 和 http_client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),  # 或直接写成 "sk-xxx"
    base_url="https://api.openai.com/v1",
    http_client=http_client
)

def generate_gmssl_code(prompt, model="gpt-4"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": f"请用 GmSSL 写一个完整 C 程序来实现：{prompt}。要求输出运行结果"}
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content
