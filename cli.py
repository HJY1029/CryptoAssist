import argparse
from assistants import openssl_helper, gmssl_helper, test_runner

def main():
    parser = argparse.ArgumentParser(description="CryptoAssist CLI")
    parser.add_argument("prompt", help="自然语言描述（如：用 AES 加密一段消息）")
    parser.add_argument("--backend", choices=["openssl", "gmssl"], default="openssl", help="选择加密后端，默认openssl")
    args = parser.parse_args()

    if args.backend == "openssl":
        code = openssl_helper.generate_openssl_code(args.prompt)
    else:
        code = gmssl_helper.generate_gmssl_code(args.prompt)

    print("🔧 生成的代码：\n", code)
    print("🧪 运行结果：\n", test_runner.run_c_code(code))

if __name__ == "__main__":
    main()
