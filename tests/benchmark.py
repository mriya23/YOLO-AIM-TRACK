import time
import sys
import os
import threading
import numpy as np

# Force Working Directory to Project Root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)

# Mock model_loader BEFORE importing main
class MockModelLoader:
    def load(self):
        return True
    def infer(self, frame, conf_thres):
        return []

sys.modules['lib.model_loader'] = type('lib.model_loader', (), {'get_model_loader': lambda: MockModelLoader()})

# Mock dxcam
class MockCamera:
    def __init__(self):
        self.is_capturing = False
    def start(self, target_fps=None, video_mode=None, region=None):
        self.is_capturing = True
    def stop(self):
        self.is_capturing = False
    def get_latest_frame(self):
        return np.random.randint(0, 255, (320, 320, 3), dtype=np.uint8)

sys.modules['dxcam'] = type('dxcam', (), {'create': lambda output_color=None: MockCamera()})

# Add Python path
sys.path.insert(0, os.path.join(project_root, "python"))
sys.path.insert(0, project_root)

from python.main import HybridOrchestrator
import python.main as main_module

# Mock win32api for right click
original_get_async_key = main_module.win32api.GetAsyncKeyState
def mock_get_async_key(key):
    if key == main_module.win32con.VK_RBUTTON:
        return 0x8000 # Simulate Held
    return 0
main_module.win32api.GetAsyncKeyState = mock_get_async_key

def benchmark():
    print("[-] Initializing Benchmark (Mocked)...")
    orch = HybridOrchestrator()
    orch.config["headless"] = True # Disable display for pure logic test
    
    print("[-] Starting Logic Loop Benchmark (1000 iterations)...")
    
    start_time = time.perf_counter()
    iterations = 1000
    
    avg_times = []
    
    for i in range(iterations):
        t1 = time.perf_counter()
        orch.run_mouse_logic(10, 10, True)
        t2 = time.perf_counter()
        avg_times.append((t2 - t1) * 1000.0) # ms
        
    total_time = time.perf_counter() - start_time
    
    avg_ms = sum(avg_times) / len(avg_times)
    max_ms = max(avg_times)
    min_ms = min(avg_times)
    p99_ms = sorted(avg_times)[int(len(avg_times)*0.99)]
    
    print(f"[RESULTS] Logic Execution Time (run_mouse_logic):")
    print(f"  Avg: {avg_ms:.4f} ms")
    print(f"  Min: {min_ms:.4f} ms")
    print(f"  Max: {max_ms:.4f} ms")
    print(f"  P99: {p99_ms:.4f} ms")
    
    print("-" * 30)
    print(f"  Theoretical Max FPS (Logic Only): {1000.0/avg_ms:.2f}")
    
    if avg_ms > 2.0:
        print("[!] FAIL: Logic is too slow (>2ms)!")
    else:
        print("[+] PASS: Logic is fast enough for 144Hz (<7ms).")
        
    orch.stop()

if __name__ == "__main__":
    benchmark()
