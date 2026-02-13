
import sys
import os
import time
import subprocess
import struct

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../python')))

from python.shared_mem import SharedMemoryManager

def smoke_test():
    print("[*] Starting Executor Smoke Test...")
    
    # 1. Initialize Shared Memory
    try:
        shm_name = "aimbot_shared_mem"
        print(f"[*] Creating SHM: {shm_name}")
        shm = SharedMemoryManager(filename=shm_name)
        # Write initial SAFE state
        shm.write_data(0, 0, False, 3.0, 1.5, False, 0.0, 0.0, 250.0, 10.0, 100, False, False)
        print("[+] SHM Created & Initialized.")
    except Exception as e:
        print(f"[!] SHM Failed: {e}")
        return

    # 2. Launch Executor
    exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../cpp/executor.exe'))
    print(f"[*] Launching: {exe_path}")
    
    if not os.path.exists(exe_path):
        print("[!] Executor not found!")
        return

    try:
        proc = subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        print(f"[+] Executor PID: {proc.pid}")
    except Exception as e:
        print(f"[!] Failed to launch executor: {e}")
        return

    # 3. Monitor Loop
    print("[*] Monitoring process for 10 seconds...")
    try:
        for i in range(10):
            if proc.poll() is not None:
                print(f"[!] CRASH DETECTED at T+{i}s. Exit Code: {proc.returncode}")
                break
            
            # Send 'Heartbeat' data
            # Mild movement data to test logic
            dx = 10 if i > 5 else 0 # Start moving after 5s
            dy = 5 if i > 5 else 0
            
            shm.write_data(dx, dy, i > 5, 5.0, 1.0, False, 0.0, 0.0, 250.0, 10.0, 100, False, False)
            print(f"    T+{i}s: Running... (Sent dx={dx})")
            time.sleep(1)
            
        if proc.poll() is None:
            print("[+] Smoke Test PASSED. Executor stayed alive.")
            print("[*] Sending Shutdown Signal...")
            shm.write_data(0, 0, False, 3.0, 1.5, False, 0.0, 0.0, 250.0, 10.0, 100, False, True)
            time.sleep(1)
            proc.terminate()
        else:
            print("[!] Smoke Test FAILED.")

    except KeyboardInterrupt:
        proc.terminate()
    finally:
        shm.close()

if __name__ == "__main__":
    smoke_test()
