
import sys
try:
    import cuda
    print(f"cuda module: {cuda}")
    print(f"cuda file: {cuda.__file__}")
    print(f"dir(cuda): {dir(cuda)}")
    
    from cuda import cudart
    print("cudart imported successfully")
except Exception as e:
    print(f"Error: {e}")
