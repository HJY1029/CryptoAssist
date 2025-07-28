import requests
import json
import subprocess
import os
import re
import sys
from retrying import retry

class RSAHelper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.algorithm = "RSA"
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.work_dir = os.path.join(os.getcwd(), "rsa_workdir")
        os.makedirs(self.work_dir, exist_ok=True)
        
        self.generated_code = None
        self.retry_count = 0
        self.max_retry = 5
        self.last_error = ""

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def _generate_c_code(self):
        """生成支持从PEM文件读取公钥的RSA加密代码"""
        system_prompt = """仅输出纯C代码，无任何其他内容！
基于OpenSSL库实现RSA加密，必须满足：

1. 头文件：
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/rsa.h>
#include <openssl/pem.h>
#include <openssl/err.h>
#include <openssl/bio.h>

2. 核心要求：
- 公钥通过PEM格式文件读取（用户输入文件路径）
- 填充模式：RSA_PKCS1_OAEP_PADDING
- 输入：PEM公钥文件路径、明文
- 输出：十六进制密文

3. 终端提示必须清晰（关键！）：
- 打印"请输入PEM格式的RSA公钥文件路径: "
- 打印"请输入要加密的明文: "
- 明确告知用户输入方式

4. 公钥处理流程：
1. 接收用户输入的公钥文件路径
2. 使用fopen打开文件
3. 用PEM_read_RSA_PUBKEY从文件加载公钥

5. 错误处理：
- 文件打开失败提示："无法打开公钥文件，请检查路径是否正确"
- 公钥解析失败提示："无法解析RSA公钥，请检查文件格式是否正确"
- 加密失败提示："RSA加密失败"
- 内存分配失败提示："内存分配失败"

6. 输出格式：
- 加密成功后打印"加密结果(十六进制): "，后跟密文

只输出C代码，无注释、无标记、无多余内容！"""

        error_feedback = ""
        if self.last_error:
            error_feedback = "修复：\n- 必须从文件读取公钥，接收用户输入的文件路径\n- 使用fopen打开文件，PEM_read_RSA_PUBKEY读取公钥\n- 确保文件操作错误处理完整"

        messages = [{"role": "system", "content": system_prompt}]
        if error_feedback:
            messages.append({"role": "user", "content": error_feedback})
        else:
            messages.append({"role": "user", "content": "生成从PEM文件读取公钥的RSA加密代码"})

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
            
            # 净化代码并确保关键逻辑
            clean_code = re.sub(r'//.*?\n|/\*.*?\*/|```c|```', '', raw_code, flags=re.DOTALL)
            
            # 确保文件读取逻辑正确
            if 'fopen' not in clean_code:
                insert_code = """
    char pubKeyPath[1024];
    FILE *pubKeyFile = NULL;
    RSA *rsa = NULL;
    unsigned char *encrypted = NULL;
    int encryptedLen;

    printf("请输入PEM格式的RSA公钥文件路径: ");
    if (fgets(pubKeyPath, sizeof(pubKeyPath), stdin) == NULL) {
        printf("读取路径失败\\n");
        return 1;
    }
    pubKeyPath[strcspn(pubKeyPath, "\\n")] = '\\0';

    pubKeyFile = fopen(pubKeyPath, "r");
    if (!pubKeyFile) {
        printf("无法打开公钥文件，请检查路径是否正确\\n");
        return 1;
    }

    rsa = PEM_read_RSA_PUBKEY(pubKeyFile, NULL, NULL, NULL);
    fclose(pubKeyFile);
    if (!rsa) {
        printf("无法解析RSA公钥，请检查文件格式是否正确\\n");
        return 1;
    }
"""
                clean_code = re.sub(r'int main\(\) \{', 'int main() {\n' + insert_code, clean_code, 1)

            self.generated_code = clean_code.strip()
            return self.generated_code, "代码生成成功"
        except Exception as e:
            return "", f"API错误: {str(e)}"

    def _compile_and_run(self, code=None):
        c_code = code or self.generated_code
        if not c_code:
            return "无代码可编译"

        # 确保提示信息正确
        c_code = c_code.replace(
            'printf("请输入PEM格式的RSA公钥',
            'printf("请输入PEM格式的RSA公钥文件路径: '
        )

        code_path = os.path.join(self.work_dir, "rsa_encrypt.c")
        with open(code_path, "w") as f:
            f.write(c_code)

        exec_path = os.path.join(self.work_dir, "rsa_encrypt")
        compile_cmd = (
            f"gcc {code_path} -o {exec_path} "
            f"-I/usr/include/openssl -L/usr/lib/x86_64-linux-gnu "
            f"-lcrypto -Wl,-rpath=/usr/lib/x86_64-linux-gnu"
        )
        compile_result = subprocess.run(
            compile_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        if compile_result.returncode != 0:
            self.last_error = compile_result.stderr
            return f"编译失败:\n{self.last_error}"

        os.chmod(exec_path, 0o755)
        print("\n📌 请输入以下加密信息：")
        try:
            # 使用交互方式运行，确保标准输入正确传递
            subprocess.run([exec_path], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, text=True)
            return "运行成功"
        except Exception as e:
            return f"运行失败: {str(e)}"

    def process(self):
        while self.retry_count < self.max_retry:
            self.retry_count += 1
            print(f"\n===== 第 {self.retry_count}/{self.max_retry} 次尝试 (RSA) =====")

            code, msg = self._generate_c_code()
            if not code:
                print(f"代码生成失败: {msg}")
                if input("重试？(y/n): ").lower() != 'y':
                    return
                continue

            print("\n📝 生成的加密代码：")
            print("-" * 70)
            print(code)
            print("-" * 70)

            result = self._compile_and_run(code)
            if result == "运行成功":
                print("✅ 加密成功")
                return

            print(f"❌ 操作失败: {result}")
            if input("重试？(y/n): ").lower() != 'y':
                return

        print(f"⚠️ 已达最大重试次数({self.max_retry})")
