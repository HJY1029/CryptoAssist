import openai
import os

def generate_openssl_code(prompt: str, model="gpt-4"):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": f"请用 OpenSSL 编写如下功能的加密代码，并包含注释：{prompt}"}],
        temperature=0.4,
    )
    return response['choices'][0]['message']['content']
