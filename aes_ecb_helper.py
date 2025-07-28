import requests
import json
import subprocess
import os
import re
import sys
from retrying import retry

class AESECBHelper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.mode = "ECB"
        self.supported_mode = "ECB"
        
        self.mode_config = {
            "encrypt_func": "AES_ecb_encrypt",
            "needs_iv": False,
            "key_length": 32
        }
        
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.work_dir = os.path.join(os.getcwd(), f"aes_ecb_workdir")
        os.makedirs(self.work_dir, exist_ok=True)
        
        self.generated_code = None
        self.retry_count = 0
        self.max_retry = 5
        self.last_error = ""
        self.compilation_errors = []
        self.code_history = []

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def _generate_c_code(self):
        """生成AES-ECB加密代码，专注于ECB模式的正确实现"""
        base_prompt = """仅输出纯C代码，实现AES-ECB加密：

1. 头文件：
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/aes.h>
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

2. 函数：
- hex_to_bytes：转换十六进制到字节数组
- pkcs7_pad：PKCS#7填充（块大小16字节）
- main：程序入口

3. 变量：
- 密钥：unsigned char key[32]
- 明文：char plaintext[1024]
- 密文：unsigned char ciphertext[1024]
- 长度变量：size_t类型

4. 输入输出：
- 密钥：提示"请输入32字节十六进制密钥（64字符）: "
- 明文：提示"请输入要加密的明文: "
- 密文：提示"密文: "，%02x格式输出

5. 加密函数：AES_ecb_encrypt

6. 注意：
- ECB模式不需要IV，禁止出现任何IV相关代码
- 禁止使用AES_MAX_KEY_LENGTH
- 不要任何注释和多余内容

只输出C代码！"""

        # 错误反馈
        error_feedback = ""
        if self.last_error:
            if "AES_MAX_KEY_LENGTH" in self.last_error:
                error_feedback = "必须使用unsigned char key[32]，绝对不能用AES_MAX_KEY_LENGTH！"

        # 构建请求
        messages = [{"role": "system", "content": base_prompt}]
        user_content = "生成符合要求的AES-ECB加密代码"
        if error_feedback:
            user_content += f"。错误修复：{error_feedback}"
        messages.append({"role": "user", "content": user_content})

        payload = {
            "model": "glm-3-turbo",
            "messages": messages,
            "temperature": 0.0
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            raw_code = response.json()["choices"][0]["message"]["content"]
            
            # 代码净化与修复
            clean_code = re.sub(
                r'//.*?\n|/\*.*?\*/|```c|```|[\u4e00-\u9fa5](?![：:])',
                '', 
                raw_code, 
                flags=re.DOTALL
            )
            # 强制替换密钥定义
            clean_code = re.sub(r'unsigned char key\[\d+\]', 'unsigned char key[32]', clean_code)
            # 强制替换int为size_t
            clean_code = re.sub(r'(?<!unsigned )int (\w+len|i)', r'size_t \1', clean_code)
            
            # 确保头文件
            required_includes = [
                '#include <stddef.h>',
                '#include <stdio.h>',
                '#include <stdlib.h>',
                '#include <string.h>',
                '#include <openssl/aes.h>',
                '#pragma GCC diagnostic ignored "-Wdeprecated-declarations"'
            ]
            clean_code = '\n'.join(required_includes) + '\n\n' + clean_code
            
            # 确保关键函数存在
            if 'hex_to_bytes' not in clean_code:
                clean_code += """
int hex_to_bytes(const char *hex, unsigned char *bytes, size_t max_len) {
    size_t len = strlen(hex);
    if (len % 2 != 0 || len / 2 > max_len) return -1;
    for (size_t i = 0; i < len; i += 2) {
        sscanf(hex + i, "%02x", (unsigned int *)&bytes[i/2]);
    }
    return len / 2;
}
"""
            if 'pkcs7_pad' not in clean_code:
                clean_code += """
void pkcs7_pad(unsigned char *data, size_t data_len, size_t block_size, unsigned char *padded, size_t *padded_len) {
    *padded_len = data_len + (block_size - data_len % block_size);
    memcpy(padded, data, data_len);
    unsigned char pad = block_size - (data_len % block_size);
    for (size_t i = data_len; i < *padded_len; i++) padded[i] = pad;
}
"""

            # 确保没有IV相关代码
            clean_code = re.sub(r'unsigned char iv\[[^\]]+\];', '', clean_code)
            clean_code = re.sub(r'char hex_iv\[[^\]]+\];', '', clean_code)
            clean_code = re.sub(r'printf\([^;]+IV[^;]+\);', '', clean_code)
            clean_code = re.sub(r'scanf\([^;]+hex_iv[^;]+\);', '', clean_code)

            self.generated_code = clean_code.strip()
            return self.generated_code, "代码生成成功"
        except Exception as e:
            return "", f"API错误: {str(e)}"

    def _compile_and_run(self, code=None):
        c_code = code or self.generated_code
        if not c_code:
            return "无代码可编译"

        # 最终净化
        c_code = c_code.replace('AES_MAX_KEY_LENGTH', '32')
        c_code = re.sub(r'//.*?\n|/\*.*?\*/', '', c_code, flags=re.DOTALL)

        # 写入文件
        code_path = os.path.join(self.work_dir, "aes_ecb_encrypt.c")
        with open(code_path, "w") as f:
            f.write(c_code)

        # 编译并运行
        exec_path = os.path.join(self.work_dir, "aes_ecb_encrypt")
        compile_cmd = f"gcc {code_path} -o {exec_path} -lcrypto -Wall"
        compile_result = subprocess.run(
            compile_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        if compile_result.returncode != 0:
            self.last_error = compile_result.stderr
            return f"编译失败: {self.last_error}"

        os.chmod(exec_path, 0o755)
        print("\n请输入加密信息：")
        try:
            subprocess.run([exec_path], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
            return "运行成功"
        except Exception as e:
            return f"运行错误: {str(e)}"

    def process(self):
        while self.retry_count < self.max_retry:
            self.retry_count += 1
            print(f"\n===== 第 {self.retry_count}/{self.max_retry} 次尝试 (AES-ECB) =====")

            code, msg = self._generate_c_code()
            if not code:
                print(f"生成失败: {msg}")
                if input("重试？(y/n): ").lower() != 'y':
                    return
                continue

            print("\n生成的代码：")
            print("-" * 70)
            print(code)
            print("-" * 70)

            result = self._compile_and_run(code)
            if result == "运行成功":
                print("✅ 加密成功")
                return

            print(f"❌ 失败: {result}")
            if self.retry_count < self.max_retry and input("重试？(y/n): ").lower() != 'y':
                return

        print("⚠️ 已达最大重试次数")

if __name__ == "__main__":
    api_key = input("请输入智谱API Key: ")
    helper = AESECBHelper(api_key)
    helper.process()
