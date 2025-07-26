# gmssl_helper.py
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # 设置你的 API 密钥

def generate_gmssl_code(prompt, model="gpt-4"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": f"请用 GmSSL 写一个完整 C 程序来实现：{prompt}。要求输出运行结果"}
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content
