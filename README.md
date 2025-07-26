# 🔐 CryptoAssist

让自然语言驱动你的加密开发：结合大模型 (OpenAI) + OpenSSL/GmSSL。

## ✨ 特点

- 💬 自然语言 → 加密 C/Python 示例代码
- 🔍 自动编译 & 运行结果反馈
- 🔄 OpenSSL vs GmSSL 行为对比测试
- 🖥️ 支持 CLI 接口，计划支持 Web UI

### ✅ 项目结构

```
arduino复制编辑CryptoAssist/
├── assistants/
│   ├── openssl_helper.py
│   ├── gmssl_helper.py
│   └── test_runner.py
│
├── examples/
│   ├── aes_openssl_example.py
│   ├── sm4_gmssl_example.py
│   └── rsa_openssl_sign_verify.py
│
├── tests/
│   ├── openssl_test_cases.sh
│   ├── gmssl_test_cases.sh
│   └── verify.py
│
├── cli.py
├── config.yaml
├── requirements.txt
└── README.md
```

| 目录 / 文件        | 作用                                    |
| ------------------ | --------------------------------------- |
| `assistants/`      | LLM 调用与后端代码生成模块              |
| `examples/`        | 示例代码目录（可作为提示模板）          |
| `tests/`           | 自动验证模块：对比 openssl/gmssl 结果   |
| `cli.py`           | 命令行入口                              |
| `config.yaml`      | 配置后端参数，如 openssl/gmssl 执行路径 |
| `README.md`        | 项目说明文档                            |
| `requirements.txt` | Python 依赖列表                         |

## 🔧 安装

### 1. Clone Repo

```bash
git clone https://github.com/HJY1029/CryptoAssist.git
cd CryptoAssist
```

### 2. Set Up Python Environment

```bash
sudo apt update && sudo apt install python3-pip python3-venv -y
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Install OpenSSL & GmSSL

#### OpenSSL

```bash
sudo apt install libssl-dev openssl
```

#### GmSSL

```bash
git clone https://github.com/guanzhi/GmSSL.git
cd ~/GmSSL

mkdir build
cd build

cmake ..
make -j$(nproc)
sudo make install

```

------

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

## 🔑 配置 OpenAI 密钥

```
export OPENAI_API_KEY=your-api-key
```

## 🚀 使用 CLI

```
python cli.py "请用 SM4 加密一段字符串" --backend gmssl
```

## 🧪 测试一致性

```
python tests/verify.py
```

## 📁 示例代码目录结构

- `examples/`：加密示例
- `assistants/`：LLM 工具
- `tests/`：脚本自动验证

## 🛡️ Supported Cryptographic Primitives

| Library | Primitive  | Algorithm |
| ------- | ---------- | --------- |
| OpenSSL | Symmetric  | AES, DES  |
| OpenSSL | Asymmetric | RSA, ECC  |
| GmSSL   | Symmetric  | SM4       |
| GmSSL   | Asymmetric | SM2       |
| GmSSL   | Hashing    | SM3       |

------

## 🧠 Example Prompts for GPT

| Goal | Prompt                                                       |
| ---- | ------------------------------------------------------------ |
| AES  | "Write Python code to encrypt a file with AES-256 using OpenSSL." |
| SM2  | "Generate GmSSL code for signing a message with SM2 private key." |
| RSA  | "Create OpenSSL RSA signature and verification flow in Python." |

------

## 
