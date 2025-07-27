import argparse
import getpass
import sys
import re

# 支持的算法与后端映射关系（包含是否需要mode参数的标记）
SUPPORTED_ALGORITHMS = {
    "openssl": {
        "RSA": {"internal_name": "rsa", "needs_mode": False},
        "AES-ECB": {"internal_name": "aes_ecb", "needs_mode": True},
        "AES-CBC": {"internal_name": "aes_cbc", "needs_mode": True},
        "DES-ECB": {"internal_name": "des_ecb", "needs_mode": True},
        "DES-CBC": {"internal_name": "des_cbc", "needs_mode": True}
    },
    "gmssl": {
        "SM4-ECB": {"internal_name": "sm4_ecb", "needs_mode": False},
        "SM4-CBC": {"internal_name": "sm4_cbc", "needs_mode": False}
    }
}

def import_helper(backend: str, algorithm: str):
    """动态导入对应的加密助手类"""
    try:
        if backend == "openssl":
            if algorithm == "rsa":
                from assistants.rsa_helper import RSAHelper
                return RSAHelper
            elif algorithm.startswith("aes"):
                from assistants.aes_helper import AESHelper
                return AESHelper
            elif algorithm.startswith("des"):
                from assistants.des_helper import DESHelper
                return DESHelper
        elif backend == "gmssl":
            if algorithm.startswith("sm4"):
                from assistants.gmssl_helper import SM4Helper
                return SM4Helper
        raise ImportError(f"不支持的{backend}后端算法: {algorithm}")
    except ImportError as e:
        print(f"❌ 导入助手类失败: {str(e)}")
        sys.exit(1)

def validate_api_key(api_key: str) -> bool:
    """验证API Key有效性（智谱API Key通常为32位以上）"""
    return bool(api_key and len(api_key) >= 32)

def main():
    parser = argparse.ArgumentParser(description='国密/通用加密工具（支持指定算法）')
    parser.add_argument(
        'algorithm', 
        type=str, 
        help=f'指定加密算法（支持列表）：\n'
             f'OpenSSL后端：{list(SUPPORTED_ALGORITHMS["openssl"].keys())}\n'
             f'GMSSL后端：{list(SUPPORTED_ALGORITHMS["gmssl"].keys())}'
    )
    parser.add_argument(
        '--backend', 
        type=str, 
        required=True, 
        choices=['openssl', 'gmssl'],
        help='加密后端（openssl/gmssl）'
    )
    parser.add_argument(
        '--debug', 
        action='store_true', 
        help='显示详细错误信息'
    )
    args = parser.parse_args()

    try:
        # 标准化算法名称（大写处理）
        algorithm_upper = args.algorithm.upper()
        
        # 验证算法是否在后端支持列表中
        if algorithm_upper not in SUPPORTED_ALGORITHMS[args.backend]:
            supported = list(SUPPORTED_ALGORITHMS[args.backend].keys())
            print(f"❌ 不支持的算法！{args.backend}后端支持：{supported}")
            sys.exit(1)
        
        # 获取算法配置（内部名称和是否需要mode）
        algo_config = SUPPORTED_ALGORITHMS[args.backend][algorithm_upper]
        internal_algo = algo_config["internal_name"]
        needs_mode = algo_config["needs_mode"]
        mode = algorithm_upper.split("-")[-1] if needs_mode else None
        
        # 显示当前选择
        print(f"🔍 已选择算法：{algorithm_upper}，后端：{args.backend}")
        if needs_mode and mode:
            print(f"🔑 加密模式：{mode}")
        print("💡 流程：AI生成代码 → 展示代码 → 执行加密")

        # 获取并验证智谱API Key
        print("\n⚠ 需要智谱API Key生成加密代码")
        api_key = None
        for attempt in range(3):
            api_key = getpass.getpass("请输入智谱API Key（输入时不显示）: ").strip()
            if not validate_api_key(api_key):
                print(f"❌ API Key无效（至少32个字符），剩余{2-attempt}次机会")
                continue
            
            confirm_key = getpass.getpass("请再次确认API Key: ").strip()
            if api_key == confirm_key:
                break
            print(f"❌ 两次输入不一致，剩余{2-attempt}次机会")
        else:
            print("❌ 多次输入错误，程序退出")
            sys.exit(1)

        # 导入助手类并初始化（根据需要传递mode参数）
        HelperClass = import_helper(args.backend, internal_algo)
        if needs_mode:
            helper = HelperClass(api_key, mode=mode)
        else:
            helper = HelperClass(api_key)  # SM4/RSA等不传递mode

        # 执行加密流程
        helper.process()

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"❌ 程序出错：{str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
