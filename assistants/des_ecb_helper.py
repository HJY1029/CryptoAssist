import requests
import json
import subprocess
import os
import re
import sys
from retrying import retry

class DESECBHelper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.mode = "ECB"
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.work_dir = os.path.join(os.getcwd(), f"des_ecb_workdir")
        os.makedirs(self.work_dir, exist_ok=True)
        
        self.generated_code = None
        self.retry_count = 0
        self.max_retry = 5
        self.last_error = ""
        self.compilation_errors = []
        self.code_history = []

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def _generate_c_code(self):
        """生成DES-ECB加密代码"""
        base_prompt = f"""仅输出纯C代码，不包含任何其他内容。
必须满足：

1. 头文件（按此顺序）：
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/des.h>
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

2. 函数：
- hex_to_bytes：转换十六进制到字节
- pkcs5_pad：PKCS#5填充（块大小8字节）
- main：程序入口

3. 变量强制要求：
- 密钥：unsigned char key[8]
- 长度变量：全部使用size_t类型
- 密钥调度表：DES_key_schedule schedule

4. 输入输出：
- 密钥：16个十六进制字符
- 明文：字符串输入（用fgets读取）
- 密文：%02x格式输出

5. 加密函数调用要求：
使用DES_ecb_encrypt，不需要IV参数

6. 禁止：
- 任何注释
- 任何自然语言
- 代码标记
- 非代码内容
- IV相关代码

只输出C代码！"""

        error_feedback = ""
        if self.last_error and "incompatible pointer type" in self.last_error:
            error_feedback = "修复以下问题，只输出纯C代码：\n"
            error_feedback += "- ECB模式不需要IV\n"
            error_feedback += "- DES_ecb_encrypt调用参数正确\n"

        messages = [{"role": "system", "content": base_prompt}]
        if error_feedback:
            messages.append({"role": "user", "content": error_feedback})
        else:
            messages.append({"role": "user", "content": "生成符合要求的DES-ECB加密代码"})

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
            
            # 代码净化
            clean_code = re.sub(
                r'//.*?\n|/\*.*?\*/|```c|```|[\u4e00-\u9fa5]',
                '', 
                raw_code, 
                flags=re.DOTALL
            )
            # 移除任何IV定义
            clean_code = re.sub(r'(DES_cblock|unsigned char) iv\[[^\]]*\];', '', clean_code)
            # 强制替换长度类型
            clean_code = re.sub(r'(?<!unsigned )int (\w+len|i)', r'size_t \1', clean_code)
            
            # 确保头文件
            required_includes = [
                '#include <stddef.h>',
                '#include <stdio.h>',
                '#include <stdlib.h>',
                '#include <string.h>',
                '#include <openssl/des.h>',
                '#pragma GCC diagnostic ignored "-Wdeprecated-declarations"'
            ]
            clean_code = '\n'.join(required_includes) + '\n\n' + clean_code
            
            # 确保关键函数
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
            if 'pkcs5_pad' not in clean_code:
                clean_code += """
void pkcs5_pad(unsigned char *data, size_t data_len, size_t block_size, unsigned char *padded, size_t *padded_len) {
    *padded_len = data_len + (block_size - data_len % block_size);
    memcpy(padded, data, data_len);
    unsigned char pad = block_size - (data_len % block_size);
    for (size_t i = data_len; i < *padded_len; i++) padded[i] = pad;
}
"""

            # 修复输入方式
            if 'fgets' not in clean_code:
                clean_code = clean_code.replace('scanf', 'fgets')
                if 'strcspn' not in clean_code:
                    clean_code = clean_code.replace('fgets(hex_key, sizeof(hex_key), stdin);', 
                                                   'fgets(hex_key, sizeof(hex_key), stdin); hex_key[strcspn(hex_key, "\\n")] = \'\\0\';')

            self.generated_code = clean_code.strip()
            return self.generated_code, "代码生成成功"
        except Exception as e:
            return "", f"API错误: {str(e)}"

    def _compile_and_run(self, code=None):
        # 实现与原DESHelper类似，移除IV相关处理
        c_code = code or self.generated_code
        if not c_code:
            return "无代码可编译"

        c_code = re.sub(r'//.*?\n|/\*.*?\*/', '', c_code, flags=re.DOTALL)
        c_code = re.sub(r'(DES_cblock|unsigned char) iv\[[^\]]*\];', '', c_code)

        code_path = os.path.join(self.work_dir, "des_ecb_encrypt.c")
        with open(code_path, "w") as f:
            f.write(c_code)

        exec_path = os.path.join(self.work_dir, "des_ecb_encrypt")
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
        # 与原DESHelper的process方法相同
        while self.retry_count < self.max_retry:
            self.retry_count += 1
            print(f"\n===== 第 {self.retry_count}/{self.max_retry} 次尝试 (DES-{self.mode}) =====")

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
