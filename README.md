# CryptoAssist - 加密算法代码生成与运行工具

CryptoAssist 是一个基于 OpenSSL、GmSSL库的加密算法代码生成与运行工具，能够自动生成多种加密算法（如 DES、AES、RSA 、SM4等）的 C 语言代码，并支持编译和运行，帮助开发者快速实现加密功能。

## 项目简介

CryptoAssist 通过调用大语言模型 API（当前使用 glm-3-turbo）生成符合规范的加密算法 C 代码，并提供自动编译和运行功能。支持多种加密模式和算法，简化了密码学相关开发的流程，特别适合需要快速验证加密逻辑的场景。

## 核心功能

- 自动生成多种加密算法的 C 语言代码
- 支持 DES 多种模式（ECB、CBC、CFB、OFB）
- 支持 DES 多种模式（ECB、CBC、CFB、OFB）
- 支持 RSA 加密算法
- 支持 SM4 加密算法
- 自动处理代码中的常见错误（如变量类型、函数参数等）
- 一键编译并运行生成的代码
- 包含错误重试机制，提高代码生成成功率

## 支持的算法与模式

| 算法 | 支持模式           | 密钥长度                      | 块大小  | 备注              |
| ---- | ------------------ | ----------------------------- | ------- | ----------------- |
| DES  | ECB, CBC, CFB, OFB | 8 字节 (64 位，含 1 位校验位) | 8 字节  | 需 OpenSSL 库支持 |
| AES  | ECB, CBC, CFB, OFB | 128/256 位                    | 16 字节 | 需 OpenSSL 库支持 |
| RSA  | -                  | 自定义（推荐 2048 位及以上）  | -       | 需 OpenSSL 库支持 |
| SM4  | ECB, CBC           | 128 位（16 字节）             | 16 字节 | 需 GmSSL 库支持   |

## 环境要求

- 操作系统：Linux 或类 Unix 系统
- 依赖工具：
  - GCC 编译器
  - OpenSSL 开发库 (`libssl-dev`)
  - Python 3.7+
  - Python 依赖：`requests`, `retrying`

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/HJY1029/CryptoAssist.git
cd CryptoAssist
```

### 2. 搭建Python环境

```bash
sudo apt update && sudo apt install python3-pip python3-venv -y
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 安装OpenSSL 和 GmSSL

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

## 使用方法

### 基本使用流程

1. 导入所需的加密助手类
2. 初始化助手实例（传入 API 密钥）
3. 调用 `process()` 方法启动代码生成、编译和运行流程

### 示例代码

#### DES-CBC 加密示例

```shell
python cli.py "DES-CBC" --backend openssl
```

> 注：API 密钥需要从 [[智谱AI开放平台](https://open.bigmodel.cn/usercenter/proj-mgmt/apikeys)](https://open.bigmodel.cn/) 获取

#### AES-CBC 加密示例

```shell
python cli.py "AES-CBC" --backend openssl
```

#### RSA 加密示例

```shell
python cli.py "RSA" --backend openssl
```

#### SM4-ECB 加密示例

```shell
python cli.py "SM4-ECB" --backend gmssl
```

程序会引导你完成：

1. 代码生成（最多尝试 5 次）
2. 代码展示
3. 编译过程
4. 输入加密所需参数（密钥、IV、明文等）
5. 输出加密结果

## 项目结构

```plaintext
CryptoAssist/
├── assistants/               # 加密助手模块
│   ├── des_cbc_helper.py     # DES-CBC模式助手
│   ├── des_cfb_helper.py     # DES-CFB模式助手
│   ├── des_ofb_helper.py     # DES-OFB模式助手
│   ├── des_ecb_helper.py     # DES-ECB模式助手
│   ├── aes_cbc_helper.py     # AES-CBC模式助手
│   ├── aes_cfb_helper.py     # AES-CFB模式助手
│   ├── aes_ofb_helper.py     # AES-OFB模式助手
│   ├── aes_ecb_helper.py     # AES-ECB模式助手
│   ├── rsa_helper.py         # RSA模式助手
│   └── gmssl_helper.py       # GMSSL助手（支持SM4-ECB,SM4-CBC）
├── des_cbc_workdir/          # DES-CBC工作目录（编译过程中生成的代码和可执行文件）
├── des_cfb_workdir/          # DES-CFB工作目录
├── des_ofb_workdir/          # DES-OFB工作目录
...
├── rsa_workdir/              # RSA工作目录
├── .env                      # API密钥配置文件
└── README.md                 # 项目说明文档
```

## 代码生成规则

生成的 C 代码遵循以下规范：

1. **头文件包含**：按固定顺序包含必要的头文件
2. **函数要求**：包含必要的辅助函数（如十六进制转换、填充函数等）
3. **变量规范**：使用正确的变量类型（如 `DES_cblock` 类型的 IV）
4. **输入输出**：统一的用户交互提示和格式化输出
5. **错误处理**：包含必要的错误检查和提示

## 错误处理与重试机制

- 代码生成失败时，支持手动选择是否重试
- 编译错误时，会提取错误信息并反馈给大语言模型，用于改进代码
- 最多尝试 5 次代码生成与编译过程
- 网络错误时，自动重试 3 次 API 调用

## 注意事项

1. 本工具生成的代码仅供学习和参考，生产环境使用需进行安全审计
2. 部分加密模式（如 ECB）安全性较低，不建议用于敏感场景
3. 确保输入的密钥和 IV 符合格式要求（通常为十六进制字符串）
4. 生成的代码依赖 OpenSSL、GMSSL 库，部分函数可能因版本不同而有所差异
5. API 调用可能产生费用，请合理使用重试机制

## 扩展与定制

如需添加新的加密算法或模式，可以：

1. 创建新的助手类，继承基础功能
2. 在 `_generate_c_code` 方法中定义新的代码生成提示词
3. 实现模式特定的代码修正逻辑
4. 调整 `_compile_and_run` 方法以适应新的代码结构

## 许可证

本项目采用 MIT 许可证，详情参见 LICENSE 文件。

## 联系方式

如有问题或建议，请联系：

- 邮箱：2823358680@qq.com
- GitHub：https://github.com/yourusername/CryptoAssist/issues
