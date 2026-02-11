import sys
import os
import time
import ctypes

# Add lib to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.mouse_controller import get_controller
from termcolor import colored

def test_mouse():
    print(colored("--- MOUSE CONTROLLER DIAGNOSTIC ---", "cyan"))
    
    # Initialize controller
    try:
        mouse = get_controller()
    except Exception as e:
        print(colored(f"[!] Critical Error initializing controller: {e}", "red"))
        return

    # Check Interception status
    if mouse.use_interception:
        print(colored("[+] Interception Driver: DETECTED & ENABLED", "green"))
    else:
        print(colored("[-] Interception Driver: NOT DETECTED (Using Fallback)", "yellow"))
        print(colored("    Reason: Import failed or driver not installed.", "yellow"))

    # Check DLL status
    if mouse.dll:
        print(colored(f"[+] Helper DLL: LOADED", "green"))
    else:
        print(colored("[-] Helper DLL: NOT LOADED", "yellow"))

    print("\n[!] WARNING: MOUSE WILL MOVE IN 3 SECONDS...")
    for i in range(3, 0, -1):
        print(f"    {i}...")
        time.sleep(1)

    print(colored("\n[>] Moving mouse +100 pixels horizontally...", "cyan"))
    
    start_x = 0
    # Try to verify movement if possible (using GetCursorPos)
    point = ctypes.wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    start_x = point.x
    
    # Move
    mouse.move_relative(100, 0)
    time.sleep(0.1)
    
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    end_x = point.x
    
    print(f"    Start X: {start_x}")
    print(f"    End X:   {end_x}")
    
    if abs((end_x - start_x) - 100) < 5:
        print(colored("[+] Movement VERIFIED (Desktop level)", "green"))
    else:
        print(colored(f"[-] Movement FAILED or Inaccurate (Delta: {end_x - start_x})", "red"))
        if not mouse.use_interception:
            print(colored("    -> Game is likely blocking SendInput. You MUST install Interception.", "red"))

    print("\n[>] Testing Click...")
    mouse.click("left")
    print(colored("[+] Click command sent", "green"))

    print(colored("\n--- END DIAGNOSTIC ---", "cyan"))
    # input("Press Enter to exit...")

if __name__ == "__main__":
    test_mouse()
