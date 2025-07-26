import openai
import os

def generate_gmssl_code(prompt: str, model="gpt-4"):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": f"请用 GmSSL 写一个完整 C 程序来实现：{prompt}。要求输出运行结果"}],
        temperature=0.4,
    )
    return response['choices'][0]['message']['content']
