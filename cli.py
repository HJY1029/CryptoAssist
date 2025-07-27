import argparse
import getpass
from assistants.openssl_helper import generate_openssl_code

def main():
    parser = argparse.ArgumentParser(description='DES加密工具 - 基于OpenSSL')
    parser.add_argument('prompt', type=str, help='加密需求描述')
    parser.add_argument('--backend', type=str, required=True, choices=['openssl'],
                       help='加密后端（仅支持openssl）')
    args = parser.parse_args()

    print("🔍 识别到算法：DES，后端：openssl")
    print("💡 提示：程序将自动处理加密流程")

    # 获取并验证API Key
    print("\n⚠️ 需要智谱API Key生成加密代码")
    while True:
        api_key = getpass.getpass("请输入智谱API Key（输入时不显示）: ").strip()
        if not api_key:
            print("❌ API Key不能为空，请重新输入")
            continue
        
        confirm_key = getpass.getpass("请再次确认API Key: ").strip()
        if api_key == confirm_key:
            break
        print("❌ 两次输入不一致，请重新输入")

    # 生成并运行加密代码
    print("\n✅ API Key验证通过，开始生成代码...")
    try:
        c_code, result = generate_openssl_code(args.prompt, "des", api_key)
        
        print("\n📝 生成的DES加密代码：")
        print("-" * 70)
        print(c_code)
        print("-" * 70)
        
        print("\n▶️ 代码运行结果：")
        print("-" * 70)
        print(result)
        print("-" * 70)

    except Exception as e:
        print(f"❌ 程序出错：{str(e)}")

if __name__ == "__main__":
    main()
    
