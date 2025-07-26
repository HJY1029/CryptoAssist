import subprocess

def run_and_capture(script_path):
    result = subprocess.run(["bash", script_path], capture_output=True, text=True)
    return result.stdout.strip()

def compare_outputs():
    openssl_out = run_and_capture("tests/openssl_test_cases.sh")
    gmssl_out = run_and_capture("tests/gmssl_test_cases.sh")
    print("OpenSSL Output:\n", openssl_out)
    print("GmSSL Output:\n", gmssl_out)
    if openssl_out == gmssl_out:
        print("✅ 输出一致")
    else:
        print("⚠️ 输出不一致")
