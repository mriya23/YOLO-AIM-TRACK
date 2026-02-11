import time
import sys
import os
import threading
import mmap

# Helper to load SHM
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, "python"))
sys.path.insert(0, project_root)

from python.shared_mem import SharedMemoryManager

def benchmark_shm():
    print("[-] Initializing Benchmark SHM (Real Write)...")
    shm = SharedMemoryManager()
    
    print("[-] Starting SHM Write Loop Benchmark (1000 iterations)...")
    print("[-] Pastikan 'executor.exe' SEDANG JALAN/TIDAK JALAN untuk membandingkan.")
    
    start_time = time.perf_counter()
    iterations = 10000
    
    avg_times = []
    
    for i in range(iterations):
        t1 = time.perf_counter()
        # WRITE REAL DATA
        shm.write_data(
            10, 10, True, 
            0, 0, False, 0, 0, 
            100, 
            raw_input=True
        )
        t2 = time.perf_counter()
        avg_times.append((t2 - t1) * 1000.0) # ms
        
    total_time = time.perf_counter() - start_time
    
    avg_ms = sum(avg_times) / len(avg_times)
    max_ms = max(avg_times)
    
    print(f"[RESULTS] SHM Write Time:")
    print(f"  Avg: {avg_ms:.4f} ms")
    print(f"  Max: {max_ms:.4f} ms")
    print(f"  Total Iterations: {iterations}")
    
    if avg_ms > 0.5:
        print("[!] FAIL: SHM Write is SLOW (>0.5ms)!")
    else:
        print("[+] PASS: SHM Write is FAST (<0.5ms).")
        
    shm.close()

if __name__ == "__main__":
    benchmark_shm()
