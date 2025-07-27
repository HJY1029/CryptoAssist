import argparse
import getpass
from assistants.openssl_helper import generate_openssl_code
from assistants.gmssl_helper import generate_gmssl_code

def detect_algorithm(prompt, backend):
    """算法识别逻辑"""
    prompt_lower = prompt.lower()
    backend_algos = {
        'openssl': ['rsa', 'des', 'aes'],
        'gmssl': ['sm4']
    }
    
    # 优先完全匹配
    for algo in backend_algos[backend]:
        if f" {algo} " in f" {prompt_lower} ":
            return algo
    
    # 部分匹配
    for algo in backend_algos[backend]:
        if algo in prompt_lower:
            return algo
            
    return backend_algos[backend][0]

def main():
    parser = argparse.ArgumentParser(description='先展示代码再加密的工具')
    parser.add_argument('prompt', type=str, help='加密需求描述')
    parser.add_argument('--backend', type=str, required=True, 
                       choices=['openssl', 'gmssl'])
    args = parser.parse_args()

    # 识别算法
    algorithm = detect_algorithm(args.prompt, args.backend)
    print(f"🔍 识别到算法：{algorithm.upper()}，后端：{args.backend}")
    print("💡 流程：先生成代码 → 展示代码 → 再进行加密操作")

    # 获取API Key
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

    # 生成代码
    print("\n✅ API Key验证通过，开始生成代码...")
    try:
        # 先生成代码
        if args.backend == 'openssl':
            c_code, _ = generate_openssl_code(args.prompt, algorithm, api_key, generate_only=True)
        else:
            c_code, _ = generate_gmssl_code(args.prompt, algorithm, api_key, generate_only=True)
        
        # 展示代码
        print("\n📝 生成的加密代码：")
        print("-" * 70)
        print(c_code)
        print("-" * 70)

        # 确认是否继续
        while True:
            choice = input("\n是否继续进行加密操作？(y/n): ").strip().lower()
            if choice in ['y', 'n']:
                break
            print("请输入y（继续）或n（退出）")

        if choice == 'n':
            print("\n已退出加密操作")
            return

        # 执行加密
        print("\n▶️ 开始加密流程：")
        if args.backend == 'openssl':
            _, result = generate_openssl_code(args.prompt, algorithm, api_key, generate_only=False, code=c_code)
        else:
            _, result = generate_gmssl_code(args.prompt, algorithm, api_key, generate_only=False, code=c_code)

        print("-" * 70)
        print(result)
        print("-" * 70)

    except Exception as e:
        print(f"❌ 程序出错：{str(e)}")

if __name__ == "__main__":
    main()
