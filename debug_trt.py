
import os
import sys

print("Checking imports...")
try:
    import tensorrt as trt
    print(f"TensorRT imported: {trt.__version__}")
except ImportError as e:
    print(f"TensorRT import failed: {e}")

try:
    from cuda import cudart
    print("CUDA Python imported")
except ImportError as e:
    print(f"CUDA Python import failed: {e}")

print("\nTesting ModelLoader...")
try:
    from lib.model_loader import get_model_loader
    loader = get_model_loader()
    print("Attempting to load model...")
    success = loader.load()
    print(f"Load success: {success}")
    if success:
        print(f"Loaded backend: {loader.backend}")
    else:
        print("Model loader failed to load ANY model")
except Exception as e:
    import traceback
    traceback.print_exc()
