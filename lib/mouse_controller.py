"""
Mouse Controller Module - Human-like Mouse Movement Engine
Uses Interception driver for anti-cheat bypass, with SendInput fallback.
"""
import os
import ctypes
import math
import random
import time
from typing import Tuple, List, Optional

# Try Interception driver first (best for anti-cheat)
try:
    import interception
    INTERCEPTION_AVAILABLE = True
    print("[+] Interception Driver: LOADED")
except ImportError:
    INTERCEPTION_AVAILABLE = False
    print("[!] Interception not available, using SendInput")

# Windows API structures (fallback)
PUL = ctypes.POINTER(ctypes.c_ulong)

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]


class MouseController:
    """Human-like mouse movement with C++ DLL Acceleration."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # Load C++ DLL
        self.dll = None
        try:
            dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../cpp/mouse/build/Release/lunar_mouse.dll")
            if os.path.exists(dll_path):
                self.dll = ctypes.CDLL(dll_path)
                print(f"[+] Loaded Lunar Mouse DLL: {dll_path}")
            else:
                 # Fallback path for development
                dll_path = "cpp/mouse/build/Release/lunar_mouse.dll"
                if os.path.exists(dll_path):
                    self.dll = ctypes.CDLL(dll_path)
                    print(f"[+] Loaded Lunar Mouse DLL: {dll_path}")
        except Exception as e:
            print(f"[!] Failed to load Mouse DLL: {e}")

        # Anti-detection settings
        self.update_config(self.config)
        
    def update_config(self, config: dict):
        """Hot-reload configuration"""
        self.config = config
        anti_detect = config.get("anti_detection", {})
        self.anti_enabled = anti_detect.get("enabled", False)
        self.velocity_variation = anti_detect.get("velocity_variation", 0.15)
        # True = pakai SendInput (DLL) dulu — banyak game yang tidak baca Interception, pakai ini
        self.use_sendinput = config.get("mouse_use_sendinput", True)
        self.use_interception = INTERCEPTION_AVAILABLE

    def move_relative(self, dx: int, dy: int, smooth: bool = True):
        """
        Move mouse relative to current position.
        Jika mouse_use_sendinput true: pakai SendInput (DLL) dulu (skala mickey).
        Else: Interception -> DLL -> SendInput.
        """
        if dx == 0 and dy == 0:
            return
        
        dx = int(dx)
        dy = int(dy)
        
        # Opsi: paksa SendInput (bagus kalau game tidak baca Interception)
        if getattr(self, "use_sendinput", False) and self.dll:
            # SendInput pakai mickeys; ~4 mickeys per pixel supaya gerakan terlihat
            self.dll.MoveRelative(dx * 4, dy * 4)
            return
        
        # Priority 1: Interception Driver (best for anti-cheat)
        if self.use_interception:
            try:
                interception.move_relative(dx, dy)
                return
            except Exception:
                pass
        
        # Priority 2: C++ DLL (SendInput)
        if self.dll:
            self.dll.MoveRelative(dx * 4, dy * 4)  # mickeys
            return
        
        # Priority 3: Pure Python SendInput
        self._send_input_move(dx * 4, dy * 4)
            
    def click(self, button="left"):
        """Execute mouse click. Priority: Interception -> DLL -> SendInput"""
        # Priority 1: Interception
        if self.use_interception:
            try:
                if button == "left":
                    interception.left_click(clicks=1, interval=0.01)
                else:
                    interception.right_click(clicks=1, interval=0.01)
                return
            except Exception:
                pass
        
        # Priority 2: C++ DLL
        if self.dll:
            btn_id = 0 if button == "left" else 1
            self.dll.Click(btn_id)
            return
        
        # Priority 3: SendInput fallback
        if button == "left":
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
            time.sleep(0.01)
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
        else:
            ctypes.windll.user32.mouse_event(0x0008, 0, 0, 0, 0)
            time.sleep(0.01)
            ctypes.windll.user32.mouse_event(0x0010, 0, 0, 0, 0)

    def _send_input_move(self, dx, dy):
        # Legacy fallback
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.mi = MouseInput(dx, dy, 0, 0x0001, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(0), ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


# Singleton
_controller: Optional[MouseController] = None

def get_controller(config: dict = None) -> MouseController:
    """Get or create mouse controller singleton"""
    global _controller
    if _controller is None:
        _controller = MouseController(config)
    elif config:
        _controller.update_config(config)
    return _controller
