import requests
import json
import subprocess
import os
import re
import getpass

class DESOpenSSLHelper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.work_dir = os.path.join(os.getcwd(), "des_workdir")
        os.makedirs(self.work_dir, exist_ok=True)

    def _generate_c_code(self):
        """生成并提取纯C代码，过滤所有说明文字"""
        system_prompt = """仅生成纯C代码，不添加任何解释说明文字！
        生成可直接编译的DES加密C程序，必须包含：
        1. 头文件：
           #include <openssl/des.h>
           #include <stdio.h>
           #include <string.h>
           #include <stdlib.h>
           #pragma GCC diagnostic ignored "-Wdeprecated-declarations"
        
        2. 核心代码：
           int main() {
               char plaintext[1024] = {0};
               unsigned char key[8] = "01234567";
               DES_cblock iv = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07};
               DES_key_schedule schedule;

               // 读取输入
               printf("请输入要加密的明文: ");
               fgets(plaintext, sizeof(plaintext), stdin);
               plaintext[strcspn(plaintext, "\\n")] = '\\0';

               // 计算长度并填充
               size_t text_len = strlen(plaintext);
               size_t padded_len = ((text_len + 7) / 8) * 8;
               unsigned char *padded = malloc(padded_len);
               memcpy(padded, plaintext, text_len);
               memset(padded + text_len, 0, padded_len - text_len);

               // 分配密文缓冲区
               unsigned char *ciphertext = malloc(padded_len);

               // 初始化密钥并加密
               DES_set_key_unchecked((const_DES_cblock*)key, &schedule);
               DES_ncbc_encrypt(padded, ciphertext, padded_len, &schedule, &iv, DES_ENCRYPT);

               // 输出结果
               printf("明文: %s\\n", plaintext);
               printf("密文(十六进制): ");
               for (size_t i = 0; i < padded_len; i++) {
                   printf("%02x", ciphertext[i]);
               }
               printf("\\n加密完成\\n");

               // 释放内存
               free(padded);
               free(ciphertext);
               return 0;
           }
        
        特别要求：只返回C代码，不添加任何其他文字、解释或说明！
        """

        payload = {
            "model": "glm-3-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "生成符合要求的DES加密C代码，只返回代码本身，不要任何解释"}
            ]
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
                timeout=30
            )
            response.raise_for_status()
            raw_code = response.json()["choices"][0]["message"]["content"]
            
            # 严格提取C代码，过滤所有非代码内容
            # 移除所有markdown标记
            code = re.sub(r'```c|\n```', '', raw_code).strip()
            # 移除可能的语言标记（如"c"）
            code = re.sub(r'^c\n', '', code)
            # 移除所有非C代码的内容（如说明文字）
            lines = code.split('\n')
            valid_lines = []
            for line in lines:
                # 保留包含C代码特征的行
                if re.search(r'#include|int main|char |unsigned char|printf|DES_|;|{|}', line):
                    valid_lines.append(line)
            return '\n'.join(valid_lines)
        except Exception as e:
            return f"代码生成失败: {str(e)}"

    def _compile_and_run(self, c_code):
        """编译并运行C代码"""
        code_path = os.path.join(self.work_dir, "des_encrypt.c")
        with open(code_path, "w") as f:
            f.write(c_code)

        exec_path = os.path.join(self.work_dir, "des_encrypt")
        compile_cmd = f"gcc {code_path} -o {exec_path} -lcrypto"
        compile_result = subprocess.run(
            compile_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        if compile_result.returncode != 0:
            return f"编译失败:\n{compile_result.stderr}"

        os.chmod(exec_path, 0o755)
        run_result = subprocess.run(
            exec_path,
            input="TestDES",
            shell=True,
            capture_output=True,
            text=True
        )
        return f"运行成功:\n{run_result.stdout}" if run_result.returncode == 0 else f"运行失败:\n{run_result.stderr}"

    def process(self):
        """完整处理流程"""
        c_code = self._generate_c_code()
        if "失败" in c_code:
            return c_code, ""
        result = self._compile_and_run(c_code)
        return c_code, result


def generate_openssl_code(prompt, algorithm, api_key):
    helper = DESOpenSSLHelper(api_key)
    return helper.process()


if __name__ == "__main__":
    api_key = getpass.getpass("输入API Key测试: ")
    code, res = generate_openssl_code("测试", "des", api_key)
    print(code)
    print(res)
    
