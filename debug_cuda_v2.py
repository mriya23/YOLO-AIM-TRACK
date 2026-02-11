
import sys
import os

try:
    import cuda
    print(f"cuda path: {cuda.__path__}")
    
    # Try direct import of bindings
    try:
        import cuda.bindings
        print(f"cuda.bindings imported: {cuda.bindings}")
    except ImportError as e:
        print(f"Failed to import cuda.bindings: {e}")

    try:
        from cuda import cudart
        print(f"cudart imported: {cudart}")
    except ImportError as e:
        print(f"Failed to import cudart from within cuda: {e}")

except ImportError as e:
    print(f"Failed to import cuda: {e}")
