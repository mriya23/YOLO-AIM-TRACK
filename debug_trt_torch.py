
import os
import sys
import numpy as np
import cv2
import time

print("Testing ModelLoader with PyTorch-TensorRT Interop...")

try:
    from lib.model_loader import get_model_loader
    loader = get_model_loader()
    
    print("\nAttempting to load model...")
    success = loader.load()
    print(f"Load success: {success}")
    
    if success:
        print(f"Loaded backend: {loader.backend}")
        
        # Create dummy image
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        
        print("\nRunning inference...")
        # Visualization
        t0 = time.time()
        dets = loader.infer(img)
        print(f"Inference time: {(time.time()-t0)*1000:.2f} ms")
        print(f"Detections: {dets}")
        
        print("\nRunning benchmark (100 iters)...")
        t0 = time.perf_counter()
        for _ in range(100):
            loader.infer(img)
        elapsed = time.perf_counter() - t0
        print(f"Benchmark: {100/elapsed:.2f} FPS")
        
    else:
        print("Model loader failed to load ANY model")
        
except Exception as e:
    import traceback
    traceback.print_exc()
