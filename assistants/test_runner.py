import subprocess
import tempfile
import os

def run_c_code(code: str, compiler="gcc", libs="-lssl -lcrypto"):
    with tempfile.TemporaryDirectory() as tmpdir:
        source_file = os.path.join(tmpdir, "code.c")
        binary_file = os.path.join(tmpdir, "code.out")
        with open(source_file, "w") as f:
            f.write(code)
        compile_cmd = f"{compiler} {source_file} -o {binary_file} {libs}"
        compile_result = subprocess.run(compile_cmd, shell=True, capture_output=True)
        if compile_result.returncode != 0:
            return f"编译失败：\n{compile_result.stderr.decode()}"
        run_result = subprocess.run(binary_file, shell=True, capture_output=True)
        return run_result.stdout.decode()
