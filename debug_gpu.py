import torch
import dxcam

def check_gpu():
    print("="*30)
    print("GPU DIAGNOSTIC TOOL")
    print("="*30)

    # 1. Check CUDA/PyTorch
    print("\n[+] Checking CUDA (PyTorch)...")
    if torch.cuda.is_available():
        cnt = torch.cuda.device_count()
        print(f"    Available CUDA Devices: {cnt}")
        for i in range(cnt):
            name = torch.cuda.get_device_name(i)
            print(f"    Device {i}: {name}")
    else:
        print("    [!] CUDA NOT AVAILABLE. Running on CPU?")
    
    # 2. Check DXCam
    print("\n[+] Checking DXCam Outputs...")
    try:
        # DXCam doesn't have a direct 'list_devices' but we can try creating instances
        # Usually checking monitors info
        import ctypes
        user32 = ctypes.windll.user32
        print(f"    Screen Resolution: {user32.GetSystemMetrics(0)}x{user32.GetSystemMetrics(1)}")
        
        # Try default
        camera = dxcam.create(output_idx=0, output_color="BGR")
        print(f"    Default DXCam Init: OK")
        # DXCam internal device info is usually hidden, but successful init means it found a display
        print(f"    Camera Backend: {camera.backend if hasattr(camera, 'backend') else 'Unknown'}")
        print(f"    Target GPU: {torch.cuda.get_device_name(0)}")
        
    except Exception as e:
        print(f"    [!] DXCam Init Failed: {e}")

if __name__ == "__main__":
    check_gpu()
