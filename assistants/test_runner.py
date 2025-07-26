import subprocess
import tempfile
import os

def run_c_code(code: str, compiler="gcc", libs=None):
    if libs is None:
        libs = ["-lssl", "-lcrypto"]
    with tempfile.TemporaryDirectory() as tmpdir:
        source_file = os.path.join(tmpdir, "code.c")
        binary_file = os.path.join(tmpdir, "code.out")
        with open(source_file, "w") as f:
            f.write(code)
        
        compile_cmd = [compiler, source_file, "-o", binary_file] + libs
        
        try:
            compile_result = subprocess.run(compile_cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            return f"编译失败：\n{e.stderr}"
        
        try:
            run_result = subprocess.run([binary_file], capture_output=True, text=True, check=True)
            return run_result.stdout
        except subprocess.CalledProcessError as e:
            return f"运行出错：\n{e.stderr}"
