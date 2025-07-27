import requests
import json
import subprocess
import os
import re

class GmSSLHelper:
    def __init__(self, api_key, algorithm):
        self.api_key = api_key
        self.algorithm = algorithm  # 仅支持SM4
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.work_dir = os.path.join(os.getcwd(), f"{algorithm}_workdir")
        os.makedirs(self.work_dir, exist_ok=True)
        self.generated_code = None

    def _generate_c_code(self):
        """生成完全匹配GmSSL 3.2.1接口的SM4代码"""
        code_template = """#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <gmssl/sm4.h>
#include <gmssl/error.h>

int main() {
    char plaintext[1024] = {0};
    uint8_t key[SM4_KEY_SIZE] = "0123456789abcdef";  // 16字节密钥
    uint8_t ctr[SM4_BLOCK_SIZE] = {0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,
                                  0x08,0x09,0x0a,0x0b,0x0c,0x0d,0x0e,0x0f};  // 16字节计数器(CTR模式)
    SM4_KEY sm4_key;

    // 读取输入
    //printf("请输入要加密的明文: ");
    fflush(stdout);
    if (fgets(plaintext, sizeof(plaintext), stdin) == NULL) {
        printf("错误：读取输入失败\\n");
        return 1;
    }
    plaintext[strcspn(plaintext, "\\n")] = '\\0';

    // 空输入检查
    if (strlen(plaintext) == 0) {
        printf("错误：明文不能为空\\n");
        return 1;
    }

    // 计算填充长度（SM4块大小16字节）
    size_t text_len = strlen(plaintext);
    size_t padded_len = ((text_len + SM4_BLOCK_SIZE - 1) / SM4_BLOCK_SIZE) * SM4_BLOCK_SIZE;
    uint8_t *padded = (uint8_t*)malloc(padded_len);
    if (!padded) {
        printf("错误：内存分配失败\\n");
        return 1;
    }
    memcpy(padded, plaintext, text_len);
    memset(padded + text_len, 0, padded_len - text_len);  // 填充0

    // 初始化加密密钥（GmSSL 3.2.1无返回值）
    sm4_set_encrypt_key(&sm4_key, key);

    // 分配密文缓冲区
    uint8_t *ciphertext = (uint8_t*)malloc(padded_len);
    if (!ciphertext) {
        printf("错误：内存分配失败\\n");
        free(padded);
        return 1;
    }

    // CTR模式加密（严格匹配GmSSL 3.2.1函数参数）
    // 函数原型：void sm4_ctr_encrypt(const SM4_KEY *key, uint8_t ctr[16], const uint8_t *in, size_t inlen, uint8_t *out)
    sm4_ctr_encrypt(&sm4_key, ctr, padded, padded_len, ciphertext);

    // 输出结果
    printf("明文: %s\\n", plaintext);
    printf("密文(十六进制): ");
    for (size_t i = 0; i < padded_len; i++) {
        printf("%02x", ciphertext[i]);
    }
    printf("\\n加密完成\\n");

    // 释放资源
    free(padded);
    free(ciphertext);
    return 0;
}
"""

        system_prompt = """生成纯C代码，严格匹配GmSSL 3.2.1的SM4接口：
        1. sm4_ctr_encrypt函数参数格式：(密钥, 计数器, 明文, 长度, 密文)
        2. 不添加多余参数，函数原型为：void sm4_ctr_encrypt(const SM4_KEY *key, uint8_t ctr[16], const uint8_t *in, size_t inlen, uint8_t *out)
        3. 使用SM4_BLOCK_SIZE和SM4_KEY_SIZE宏
        4. 只返回可编译的纯代码，无注释和解释"""

        payload = {
            "model": "glm-3-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"生成SM4加密代码，基于模板：\n{code_template}"}
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
            
            clean_code = re.sub(r'```c|\n```|//.*$', '', raw_code, flags=re.MULTILINE)
            self.generated_code = clean_code.strip()
            return self.generated_code, "代码生成完成"
        except Exception as e:
            return "", f"API请求失败: {str(e)}"

    def _compile_and_run(self, code=None):
        c_code = code or self.generated_code
        if not c_code:
            return "没有有效的代码可运行"

        code_path = os.path.join(self.work_dir, "sm4_encrypt.c")
        with open(code_path, "w") as f:
            f.write(c_code)

        exec_path = os.path.join(self.work_dir, "sm4_encrypt")
        compile_cmd = (
            f"gcc {code_path} -o {exec_path} "
            f"-I/usr/local/include -L/usr/local/lib "
            f"-lgmssl -Wl,-rpath=/usr/local/lib"
        )

        compile_result = subprocess.run(
            compile_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        if compile_result.returncode != 0:
            return (f"编译失败:\n{compile_result.stderr}\n"
                    f"确认GmSSL版本正确：\n"
                    f"cd GmSSL && git checkout v3.2.1 && make clean && make && sudo make install\n"
                    f"sudo ldconfig /usr/local/lib")

        os.chmod(exec_path, 0o755)
        print("\n📌 请在下方输入要加密的明文：")
        try:
            exit_code = os.system(exec_path)
            return "加密完成" if exit_code == 0 else f"运行出错，退出代码: {exit_code}"
        except Exception as e:
            return f"运行失败: {str(e)}"

    def process(self, generate_only=True, code=None):
        if generate_only:
            return self._generate_c_code()
        else:
            result = self._compile_and_run(code)
            return "", result


def generate_gmssl_code(prompt, algorithm, api_key, generate_only=True, code=None):
    helper = GmSSLHelper(api_key, algorithm)
    return helper.process(generate_only, code)
