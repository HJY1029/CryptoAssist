import requests
import json
import subprocess
import tempfile
import os
import re

class GmSSLHelper:
    def __init__(self, api_key):
        if not self._validate_api_key(api_key):
            raise ValueError("API Key格式无效（长度需至少32位）")
        self.api_key = api_key
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.temp_dir = tempfile.TemporaryDirectory()

    # 关键修改：仅验证长度
    def _validate_api_key(self, api_key):
        """仅验证API Key长度是否≥32位，不限制字符类型"""
        return bool(api_key and len(api_key) >= 32)

    def extract_c_code(self, raw_text):
        start_tag = "```c"
        end_tag = "```"
        start_idx = raw_text.find(start_tag)
        end_idx = raw_text.find(end_tag, start_idx + len(start_tag))
        
        if start_idx != -1 and end_idx != -1:
            return raw_text[start_idx + len(start_tag) : end_idx].strip()
        return raw_text.strip()

    def fix_syntax_errors(self, code):
        lines = code.split('\n')
        fixed_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.endswith((';', '{', '}', '//')) and '#' not in stripped:
                line += ';'
            fixed_lines.append(line)
        code = '\n'.join(fixed_lines)
        
        if 'SM4_KEY' in code and 'len' not in code:
            code = re.sub(r'(unsigned char plaintext.*;)', r'\1\n    size_t len = strlen((const char *)plaintext);', code)
        
        if 'fgets(plaintext' not in code:
            input_code = """
    printf("请输入要加密的明文: ");
    fgets(plaintext, sizeof(plaintext), stdin);
    plaintext[strcspn(plaintext, "\\n")] = '\\0';
"""
            code = re.sub(r'(int main\(\)\s*\{\s*)', r'\1char plaintext[1024];\n' + input_code, code)
        
        return code

    def generate_c_code(self, prompt):
        payload = {
            "model": "glm-3-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": """生成基于GmSSL的SM4加密C程序，包含：
                    1. 头文件：#include <gmssl/sm4.h>、#include <stdio.h>、#include <string.h>
                    2. 终端输入明文
                    3. 正确的密钥和缓冲区定义
                    4. 完整的加密流程
                    5. 输出明文和十六进制密文
                    """
                },
                {"role": "user", "content": prompt}
            ],
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
                data=json.dumps(payload),
                timeout=30
            )
            response_data = response.json()
            
            if response.status_code == 200 and "choices" in response_data:
                raw_code = response_data["choices"][0]["message"]["content"]
                clean_code = self.extract_c_code(raw_code)
                return self.fix_syntax_errors(clean_code)
            else:
                return f"API错误：{response_data.get('error', {}).get('message', '未知错误')}"
        except Exception as e:
            return f"生成失败：{str(e)}"

    def compile_and_run(self, code):
        if not code or code.startswith(("API错误", "生成失败")):
            return "代码生成失败，无法编译运行"
        
        code_path = os.path.join(self.temp_dir.name, "sm4_code.c")
        exec_path = os.path.join(self.temp_dir.name, "sm4_exec")
        
        with open(code_path, "w") as f:
            f.write(code)
        
        compile_cmd = f"gcc {code_path} -o {exec_path} -lgmssl"
        compile_result = subprocess.run(
            compile_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if compile_result.returncode != 0:
            return f"编译失败：\n{compile_result.stderr}"
        
        run_result = subprocess.run(
            exec_path,
            shell=True,
            capture_output=True,
            text=True
        )
        
        return f"运行成功：\n{run_result.stdout}" if run_result.returncode == 0 else f"运行失败：\n{run_result.stderr}"


def generate_gmssl_code(prompt, api_key):
    try:
        helper = GmSSLHelper(api_key)
        c_code = helper.generate_c_code(prompt)
        
        if not c_code.startswith(("API错误", "生成失败")):
            run_result = helper.compile_and_run(c_code)
            return c_code, run_result
        return c_code, "未生成可编译代码"
    except ValueError as e:
        return "", f"API Key错误：{str(e)}"
    except Exception as e:
        return "", f"程序错误：{str(e)}"
    

