import time
from shared_mem import SharedMemoryManager
import subprocess
import os

def smoke_test():
    print("[*] Starting IPC Smoke Test...")
    
    # Start C++ executor in a separate process
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cpp_exe = os.path.join(script_dir, "..", "cpp", "executor.exe")
    if not os.path.exists(cpp_exe):
        # Try relative to CWD if __file__ is weird
        cpp_exe = os.path.join("cpp", "executor.exe")
        if not os.path.exists(cpp_exe):
            print(f"[!] executor.exe not found at {cpp_exe}. Build it first!")
            return

    # Initialize SHM first so C++ can open it
    shm = SharedMemoryManager()
    
    print("[*] Launching C++ Executor...")
    # Using shell=True only on windows if needed, but direct path is better
    executor_proc = subprocess.Popen([cpp_exe], creationflags=subprocess.CREATE_NEW_CONSOLE)
    
    time.sleep(2) # Give C++ time to connect
    
    try:
        print("[*] Sending test movement signals for 5 seconds...")
        for i in range(50):
            # Simulate a target jumping around center
            x = (i % 10) - 5
            y = (i % 6) - 3
            # x, y, found, smoothing, humanization, rcs, rcs_x, rcs_y, fov
            shm.write_data(x, y, True, 1.0, 1.5, True, 0.5, 2.0, 100)
            time.sleep(0.1)
            
        print("[*] Stopping test...")
        shm.write_data(0, 0, False, 0, 0, False, 0, 0, 0, shutdown=True)
        
    finally:
        shm.close()
        executor_proc.terminate()
        print("[+] Smoke Test Finished.")

if __name__ == "__main__":
    smoke_test()
