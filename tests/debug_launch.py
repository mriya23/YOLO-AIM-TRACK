import subprocess
import time
import os
import sys
import threading

def read_output(process, name):
    for line in iter(process.stdout.readline, b''):
        print(f"[{name}] {line.decode().strip()}")
    # for line in iter(process.stderr.readline, b''):
    #     print(f"[{name}] ERR: {line.decode().strip()}")

def main():
    print("[-] Debugging Launch Sequence...")
    
    # 1. Launch Python
    py_script = os.path.join("python", "main.py")
    print(f"[-] Launching Python: {py_script}")
    
    # Force headless and no raw input for testing connection
    # os.environ['HEADLESS'] = '1'
    
    proc_py = subprocess.Popen(
        ["python", py_script], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        cwd=os.getcwd()
    )
    
    t_py = threading.Thread(target=read_output, args=(proc_py, "PYTHON"))
    t_py.daemon = True
    t_py.start()
    
    print("[-] Waiting 3 seconds for SHM...")
    time.sleep(3)
    
    # 2. Launch C++
    cpp_exe = os.path.join("cpp", "executor.exe")
    print(f"[-] Launching C++: {cpp_exe}")
    
    proc_cpp = subprocess.Popen(
        [cpp_exe], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        cwd=os.getcwd()
    )
    
    t_cpp = threading.Thread(target=read_output, args=(proc_cpp, "CPP"))
    t_cpp.daemon = True
    t_cpp.start()
    
    try:
        while True:
            time.sleep(1)
            if proc_py.poll() is not None:
                print(f"[!] Python Exited with code {proc_py.returncode}")
                # print stderr
                print(proc_py.stderr.read().decode())
                break
            if proc_cpp.poll() is not None:
                print(f"[!] C++ Exited with code {proc_cpp.returncode}")
                # print stderr
                print(proc_cpp.stderr.read().decode())
                break
    except KeyboardInterrupt:
        print("\nStopping...")
        proc_py.terminate()
        proc_cpp.terminate()

if __name__ == "__main__":
    main()
