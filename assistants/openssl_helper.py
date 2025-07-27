import requests
import json
import subprocess
import os
import re

class OpenSSLHelper:
    def __init__(self, api_key, algorithm):
        self.api_key = api_key
        self.algorithm = algorithm
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.work_dir = os.path.join(os.getcwd(), f"{algorithm}_workdir")
        os.makedirs(self.work_dir, exist_ok=True)
        self.generated_code = None

    def _generate_c_code(self):
        """生成指定算法的C代码"""
        configs = {
            'rsa': {
                'headers': '#include <openssl/rsa.h>\n#include <openssl/pem.h>\n#include <openssl/rand.h>',
                'template': self._get_rsa_template()
            },
            'des': {
                'headers': '#include <openssl/des.h>',
                'template': self._get_des_template()
            },
            'aes': {
                'headers': '#include <openssl/aes.h>',
                'template': self._get_aes_template()
            }
        }
        cfg = configs[self.algorithm]

        system_prompt = """只返回纯C代码，不添加任何解释、注释或markdown标记。
        代码必须可编译，包含完整的main函数，支持用户输入明文并输出加密结果。"""

        payload = {
            "model": "glm-3-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": cfg['template'].format(headers=cfg['headers'])}
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        raw_code = response.json()["choices"][0]["message"]["content"]
        
        # 净化代码
        clean_code = re.sub(r'```c|\n```|//.*$', '', raw_code, flags=re.MULTILINE)
        self.generated_code = clean_code.strip()
        return self.generated_code

    def _compile_and_run(self, code=None):
        """编译并运行代码"""
        c_code = code or self.generated_code
        if not c_code:
            return "没有有效的代码可运行"

        # 保存代码
        code_path = os.path.join(self.work_dir, f"{self.algorithm}_encrypt.c")
        with open(code_path, "w") as f:
            f.write(c_code)

        # 编译
        exec_path = os.path.join(self.work_dir, f"{self.algorithm}_encrypt")
        compile_cmd = f"gcc {code_path} -o {exec_path} -lcrypto"
        compile_result = subprocess.run(
            compile_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        if compile_result.returncode != 0:
            return f"编译失败:\n{compile_result.stderr}\n请安装OpenSSL: sudo apt install libssl-dev"

        # 运行加密
        os.chmod(exec_path, 0o755)
        print("\n📌 请在下方输入要加密的明文：")
        try:
            exit_code = os.system(exec_path)
            return "加密完成" if exit_code == 0 else f"加密出错，退出代码: {exit_code}"
        except Exception as e:
            return f"运行失败: {str(e)}"

    def _get_rsa_template(self):
        return """#include <stdio.h>
#include <string.h>
#include <stdlib.h>
{headers}
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

int main() {{
    char plaintext[1024] = {{0}};
    unsigned char *ciphertext = NULL;
    int ciphertext_len;
    RSA *rsa = NULL;

    // 生成RSA密钥
    rsa = RSA_generate_key(2048, RSA_F4, NULL, NULL);
    if (!rsa) {{
        printf("错误：生成RSA密钥失败\\n");
        return 1;
    }}

    // 输入明文
    //printf("请输入要加密的明文(最长%d字节): ", RSA_size(rsa) - 42);
    fflush(stdout);
    if (fgets(plaintext, sizeof(plaintext), stdin) == NULL) {{
        printf("错误：读取输入失败\\n");
        RSA_free(rsa);
        return 1;
    }}
    plaintext[strcspn(plaintext, "\\n")] = '\\0';

    // 空输入检查
    if (strlen(plaintext) == 0) {{
        printf("错误：明文不能为空\\n");
        RSA_free(rsa);
        return 1;
    }}

    // 长度检查
    if (strlen(plaintext) > (size_t)(RSA_size(rsa) - 42)) {{
        printf("错误：明文过长，最长支持%d字节\\n", RSA_size(rsa) - 42);
        RSA_free(rsa);
        return 1;
    }}

    // 分配缓冲区
    ciphertext = (unsigned char*)malloc(RSA_size(rsa));
    if (!ciphertext) {{
        printf("内存分配失败\\n");
        RSA_free(rsa);
        return 1;
    }}

    // 加密
    ciphertext_len = RSA_public_encrypt(
        strlen(plaintext) + 1,
        (unsigned char*)plaintext,
        ciphertext,
        rsa,
        RSA_PKCS1_PADDING
    );
    if (ciphertext_len == -1) {{
        printf("错误：RSA加密失败\\n");
        free(ciphertext);
        RSA_free(rsa);
        return 1;
    }}

    // 输出结果
    printf("明文: %%s\\n", plaintext);
    printf("密文(十六进制): ");
    for (int i = 0; i < ciphertext_len; i++) {{
        printf("%%02x", ciphertext[i]);
    }}
    printf("\\n加密完成\\n");

    // 清理
    free(ciphertext);
    RSA_free(rsa);
    return 0;
}}
"""  # 修复：添加缺失的终止符

    def _get_des_template(self):
        return """#include <stdio.h>
#include <string.h>
#include <stdlib.h>
{headers}
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

int main() {{
    char plaintext[1024] = {{0}};
    unsigned char key[8] = "01234567";
    DES_cblock iv = {{0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07}};
    DES_key_schedule schedule;

    // 输入明文
    //printf("请输入要加密的明文: ");
    fflush(stdout);
    fgets(plaintext, sizeof(plaintext), stdin);
    plaintext[strcspn(plaintext, "\\n")] = '\\0';

    if (strlen(plaintext) == 0) {{
        printf("错误：明文不能为空\\n");
        return 1;
    }}

    // 填充处理
    size_t text_len = strlen(plaintext);
    size_t padded_len = ((text_len + 7) / 8) * 8;
    unsigned char *padded = malloc(padded_len);
    if (!padded) {{
        printf("内存分配失败\\n");
        return 1;
    }}
    memcpy(padded, plaintext, text_len);
    memset(padded + text_len, 0, padded_len - text_len);

    // 加密
    unsigned char *ciphertext = malloc(padded_len);
    if (!ciphertext) {{
        printf("内存分配失败\\n");
        free(padded);
        return 1;
    }}
    DES_set_key_unchecked((const DES_cblock*)key, &schedule);
    DES_ncbc_encrypt(padded, ciphertext, padded_len, &schedule, &iv, DES_ENCRYPT);

    // 输出
    printf("明文: %%s\\n", plaintext);
    printf("密文(十六进制): ");
    for (size_t i = 0; i < padded_len; i++) {{
        printf("%%02x", ciphertext[i]);
    }}
    printf("\\n加密完成\\n");

    // 清理
    free(padded);
    free(ciphertext);
    return 0;
}}
"""

    def _get_aes_template(self):
        return """#include <stdio.h>
#include <string.h>
#include <stdlib.h>
{headers}
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

int main() {{
    char plaintext[1024] = {{0}};
    unsigned char key[16] = "0123456789abcdef";
    unsigned char iv[16] = {{0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0a,0x0b,0x0c,0x0d,0x0e,0x0f}};
    AES_KEY schedule;

    // 输入明文
    //printf("请输入要加密的明文: ");
    fflush(stdout);
    fgets(plaintext, sizeof(plaintext), stdin);
    plaintext[strcspn(plaintext, "\\n")] = '\\0';

    if (strlen(plaintext) == 0) {{
        printf("错误：明文不能为空\\n");
        return 1;
    }}

    // 填充处理
    size_t text_len = strlen(plaintext);
    size_t padded_len = ((text_len + 15) / 16) * 16;
    unsigned char *padded = malloc(padded_len);
    if (!padded) {{
        printf("内存分配失败\\n");
        return 1;
    }}
    memcpy(padded, plaintext, text_len);
    memset(padded + text_len, 0, padded_len - text_len);

    // 加密
    unsigned char *ciphertext = malloc(padded_len);
    if (!ciphertext) {{
        printf("内存分配失败\\n");
        free(padded);
        return 1;
    }}
    AES_set_encrypt_key(key, 128, &schedule);
    AES_cbc_encrypt(padded, ciphertext, padded_len, &schedule, iv, AES_ENCRYPT);

    // 输出
    printf("明文: %%s\\n", plaintext);
    printf("密文(十六进制): ");
    for (size_t i = 0; i < padded_len; i++) {{
        printf("%%02x", ciphertext[i]);
    }}
    printf("\\n加密完成\\n");

    // 清理
    free(padded);
    free(ciphertext);
    return 0;
}}
"""

    def process(self, generate_only=True, code=None):
        """处理流程控制"""
        if generate_only:
            c_code = self._generate_c_code()
            return c_code, "代码生成完成"
        else:
            result = self._compile_and_run(code)
            return "", result


def generate_openssl_code(prompt, algorithm, api_key, generate_only=True, code=None):
    helper = OpenSSLHelper(api_key, algorithm)
    return helper.process(generate_only, code)
