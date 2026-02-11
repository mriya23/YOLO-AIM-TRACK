"""
Lunar Aimbot - C++ Engine Hybrid
Detection (DXCam + TensorRT) runs in Python.
Aim loop runs in C++ DLL (144Hz); mouse output via Python + Interception with batching for stable FPS when locked.
"""
import ctypes
import cv2
import dxcam
import json
import math
import numpy as np
import os
import sys
import time
import threading
import winsound
import win32api
import win32con

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uuid
_script_dir = os.path.dirname(os.path.abspath(__file__))
DEBUG_LOG_PATH = os.path.join(_script_dir, ".cursor", "debug.log")

def _debug_log(location, message, data, hypothesis_id):
    try:
        log_dir = os.path.dirname(DEBUG_LOG_PATH)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": str(uuid.uuid4())[:8], "timestamp": int(time.time() * 1000), "location": location, "message": message, "data": data, "hypothesisId": hypothesis_id}, default=str) + "\n")
    except Exception:
        pass

from termcolor import colored
from lib.mouse_controller import get_controller
from lib.model_loader import get_model_loader

# ============================================================================
# C++ DLL LOADER
# ============================================================================
def _load_dll():
    """Load lunar_aimbot.dll from cpp/aimbot/build/Release/"""
    base = os.path.dirname(os.path.abspath(__file__))
    dll_paths = [
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v17.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v16.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v15.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v14.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v13.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v12.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v11.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v10.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v9.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v8.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v6.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v5.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v4.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v3.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot_v2.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "Release", "lunar_aimbot.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "lunar_aimbot_v2.dll"),
        os.path.join(base, "cpp", "aimbot", "build", "lunar_aimbot.dll"),
    ]
    for p in dll_paths:
        if os.path.exists(p):
            try:
                dll = ctypes.CDLL(p)
                print(colored(f"[+] C++ Aimbot DLL: LOADED ({p})", "green"))
                
                # Setup function signatures
                dll.AimbotCreate.argtypes = [ctypes.c_char_p]
                dll.AimbotCreate.restype = ctypes.c_void_p
                
                dll.AimbotDestroy.argtypes = [ctypes.c_void_p]
                dll.AimbotDestroy.restype = None
                
                dll.AimbotStartAimLoop.argtypes = [ctypes.c_void_p]
                dll.AimbotStartAimLoop.restype = None
                
                dll.AimbotStopAimLoop.argtypes = [ctypes.c_void_p]
                dll.AimbotStopAimLoop.restype = None
                
                dll.AimbotPushDetections.argtypes = [
                    ctypes.c_void_p,
                    ctypes.POINTER(ctypes.c_double), ctypes.c_int,
                    ctypes.c_int, ctypes.c_int, ctypes.c_int
                ]
                dll.AimbotPushDetections.restype = None
                
                dll.AimbotSetScreenCenter.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
                dll.AimbotSetScreenCenter.restype = None
                
                dll.AimbotToggle.argtypes = [ctypes.c_void_p]
                dll.AimbotToggle.restype = None
                
                dll.AimbotIsEnabled.argtypes = [ctypes.c_void_p]
                dll.AimbotIsEnabled.restype = ctypes.c_int
                
                dll.AimbotIsRunning.argtypes = [ctypes.c_void_p]
                dll.AimbotIsRunning.restype = ctypes.c_int
                
                dll.AimbotGetFPS.argtypes = [ctypes.c_void_p]
                dll.AimbotGetFPS.restype = ctypes.c_int
                
                dll.AimbotGetTargetData.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double)]
                dll.AimbotGetTargetData.restype = None
                
                dll.AimbotReloadConfig.argtypes = [ctypes.c_void_p]
                dll.AimbotReloadConfig.restype = None
                
                dll.AimbotPopMouseCommands.argtypes = [
                    ctypes.c_void_p,
                    ctypes.POINTER(ctypes.c_int),
                    ctypes.POINTER(ctypes.c_int),
                    ctypes.POINTER(ctypes.c_int)
                ]
                dll.AimbotPopMouseCommands.restype = None
                
                dll.AimbotGetLastTargetValid.argtypes = [ctypes.c_void_p]
                dll.AimbotGetLastTargetValid.restype = ctypes.c_int
                
                return dll
            except Exception as e:
                print(colored(f"[!] Failed to load DLL: {e}", "yellow"))
    
    print(colored("[X] lunar_aimbot.dll NOT FOUND! Run build_aimbot.bat first.", "red"))
    print(colored("[X] Looked in:", "red"))
    for p in dll_paths:
        print(colored(f"    {p}", "red"))
    return None

DLL = _load_dll()

# DPI Awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

print(colored("[+] DXCam Screen Capture: LOADED", "green"))


class Aimbot:
    """C++ Engine Aimbot — Python detection + C++ aim loop"""
    config = {}
    config_path = "lib/config/config.json"
    last_config_mtime = 0
    aimbot_enabled = True
    status_display_time = 0
    _push_log_ct = 0

    @classmethod
    def load_config(cls):
        try:
            with open(cls.config_path, 'r') as f:
                cls.config = json.load(f)
            cls.last_config_mtime = os.path.getmtime(cls.config_path)
        except Exception as e:
            cls.config = {}

    @classmethod
    def reload_config_if_changed(cls):
        try:
            mtime = os.path.getmtime(cls.config_path)
            if mtime > cls.last_config_mtime:
                cls.load_config()
        except: pass

    def __init__(self):
        if DLL is None:
            raise RuntimeError("lunar_aimbot.dll not loaded! Run build_aimbot.bat first.")
        
        self.camera = dxcam.create(output_color="BGR")
        Aimbot.load_config()
        self.model_loader = get_model_loader()
        
        if not self.model_loader.load() or not self.model_loader.validate():
            sys.exit(1)
        
        self.roi_size = Aimbot.config.get("roi_size", 320)
        self.screen_center_x = ctypes.windll.user32.GetSystemMetrics(0) // 2
        self.screen_center_y = ctypes.windll.user32.GetSystemMetrics(1) // 2
        
        # Create mouse controller (uses Interception driver)
        self.mouse = get_controller(Aimbot.config)
        
        # Create C++ engine
        config_path_bytes = os.path.abspath(Aimbot.config_path).encode('utf-8')
        self.engine = DLL.AimbotCreate(config_path_bytes)
        DLL.AimbotSetScreenCenter(self.engine, self.screen_center_x, self.screen_center_y)
        
        self.frame_count = 0
        self.running = False
        self.current_fps = 0
        self.display_data = None
        
        # Buffers for C++ communication
        self._target_buf = (ctypes.c_double * 7)()
        self._mouse_dx = ctypes.c_int()
        self._mouse_dy = ctypes.c_int()
        self._mouse_click = ctypes.c_int()
        
        print(colored("[+] C++ Aimbot Engine: INITIALIZED", "green"))

    def __del__(self):
        if hasattr(self, 'engine') and self.engine:
            DLL.AimbotDestroy(self.engine)
            self.engine = None

    def get_detection_box(self):
        return {
            'left': self.screen_center_x - self.roi_size // 2,
            'top': self.screen_center_y - self.roi_size // 2,
            'width': self.roi_size, 'height': self.roi_size
        }

    def _push_detections_to_cpp(self, dets, box):
        """Convert Python detections to C++ format and push"""
        if not dets:
            return
        # #region agent log
        Aimbot._push_log_ct += 1
        if Aimbot._push_log_ct % 5 == 1:
            first = dets[0]
            _debug_log("aimbot.py:_push_detections_to_cpp", "push_detections", {"count": len(dets), "roi_left": box["left"], "roi_top": box["top"], "roi_size": self.roi_size, "first_bbox": [first[0], first[1], first[2], first[3]]}, "H4")
        # #endregion
        count = len(dets)
        flat = (ctypes.c_double * (count * 5))()
        for i, det in enumerate(dets):
            x1, y1, x2, y2, conf = det
            flat[i * 5 + 0] = float(x1)
            flat[i * 5 + 1] = float(y1)
            flat[i * 5 + 2] = float(x2)
            flat[i * 5 + 3] = float(y2)
            flat[i * 5 + 4] = float(conf)
        DLL.AimbotPushDetections(
            self.engine, flat, count,
            box['left'], box['top'], self.roi_size
        )

    def draw(self, frame, fps, dets):
        """Draw overlay (runs in Python display thread)"""
        aim_fps = DLL.AimbotGetFPS(self.engine)
        cv2.putText(frame, f"DET:{fps} AIM:{aim_fps}", (5, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        fov = Aimbot.config.get("fov_radius", 150)
        c = self.roi_size // 2
        cv2.circle(frame, (c, c), fov, (0, 255, 255), 1)

        if dets:
            for x1, y1, x2, y2, _ in dets:
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 1)

        # Get target position from C++
        DLL.AimbotGetTargetData(self.engine, self._target_buf)
        tx, ty, active = self._target_buf[0], self._target_buf[1], self._target_buf[2]
        # #region agent log
        if not hasattr(self, "_draw_log_ct"): self._draw_log_ct = 0
        self._draw_log_ct += 1
        if self._draw_log_ct % 5 == 0:
            last_valid = DLL.AimbotGetLastTargetValid(self.engine) if DLL else 0
            _debug_log("aimbot.py:draw", "target_data", {"tx": tx, "ty": ty, "active": active, "last_target_valid": last_valid}, "H1,H2,H3,H5")
        # #endregion
        if active > 0.5:
            box = self.get_detection_box()
            cv2.circle(frame, (int(tx - box['left']), int(ty - box['top'])), 4, (0, 255, 0), -1)

    def detection_loop(self):
        """Python detection loop: DXCam capture + TensorRT inference → push to C++"""
        self.camera.start(target_fps=144, video_mode=True)
        box = self.get_detection_box()
        conf_check = 0

        frame_counter = 0
        start_counter = time.perf_counter()

        while self.running:
            t_start = time.perf_counter()

            # Config reload
            if t_start - conf_check > 1.0:
                Aimbot.reload_config_if_changed()
                box = self.get_detection_box()
                conf_check = t_start

            # FPS counter
            if t_start - start_counter >= 1.0:
                self.current_fps = frame_counter
                frame_counter = 0
                start_counter = t_start

            # Check if C++ engine stopped (F2 pressed)
            if not DLL.AimbotIsRunning(self.engine):
                self.running = False
                break

            # Capture
            frame = self.camera.get_latest_frame()
            if frame is None:
                region = (box['left'], box['top'], box['left']+box['width'], box['top']+box['height'])
                frame = self.camera.grab(region=region)
                if frame is None:
                    continue
            else:
                frame = frame[box['top']:box['top']+box['height'], box['left']:box['left']+box['width']]

            # YOLO Inference (GPU, not GIL bottleneck)
            dets = self.model_loader.infer(frame, Aimbot.config.get("conf_thres", 0.45))

            # Push detections to C++ engine
            self._push_detections_to_cpp(dets, box)

            # Display buffer
            if not Aimbot.config.get("headless", False):
                self.display_data = (frame, dets)

            frame_counter += 1

    def mouse_output_loop(self):
        """Poll C++ deltas → send via Interception directly (minimal overhead)."""
        # v15: Use Interception directly to avoid:
        #   - lunar_mouse.dll overhead (separate DLL load + SendInput)
        #   - 4× mickey multiplier in MouseController (was causing 4× overshoot!)
        #   - GIL contention from too-frequent Python calls
        # Poll at ~333Hz (3ms) instead of 1000Hz to reduce GIL pressure on detection thread.
        
        use_interception = False
        try:
            import interception
            use_interception = True
        except ImportError:
            pass
        
        while self.running:
            DLL.AimbotPopMouseCommands(
                self.engine,
                ctypes.byref(self._mouse_dx),
                ctypes.byref(self._mouse_dy),
                ctypes.byref(self._mouse_click)
            )
            dx = self._mouse_dx.value
            dy = self._mouse_dy.value
            click = self._mouse_click.value
            if click:
                self.mouse.click("left")
            if dx != 0 or dy != 0:
                if use_interception:
                    interception.move_relative(dx, dy)  # Direct! No 4× multiplier!
                else:
                    self.mouse.move_relative(dx, dy)
            time.sleep(0.003)  # 333Hz — smooth enough, less GIL pressure
        return
        
        # With batching (for stable FPS)
        acc_dx, acc_dy = 0, 0
        last_flush = time.perf_counter()
        last_move_time = time.perf_counter()
        while self.running:
            DLL.AimbotPopMouseCommands(
                self.engine,
                ctypes.byref(self._mouse_dx),
                ctypes.byref(self._mouse_dy),
                ctypes.byref(self._mouse_click)
            )
            dx = self._mouse_dx.value
            dy = self._mouse_dy.value
            click = self._mouse_click.value
            if click:
                self.mouse.click("left")
            if dx != 0 or dy != 0:
                acc_dx += dx
                acc_dy += dy
                last_move_time = time.perf_counter()
            now = time.perf_counter()
            # Flush if: interval passed OR accumulated move is large enough OR no new moves for 5ms (force flush)
            should_flush = (now - last_flush) >= BATCH_INTERVAL or \
                          (abs(acc_dx) >= BATCH_THRESHOLD or abs(acc_dy) >= BATCH_THRESHOLD) or \
                          ((now - last_move_time) > 0.005 and (acc_dx != 0 or acc_dy != 0))
            if should_flush and (acc_dx != 0 or acc_dy != 0):
                self.mouse.move_relative(acc_dx, acc_dy)
                acc_dx, acc_dy = 0, 0
                last_flush = now
            time.sleep(0.001)

    def display_loop(self):
        """Decoupled rendering (Python, non-critical path)"""
        while self.running:
            if self.display_data:
                frame, dets = self.display_data
                self.display_data = None
                self.draw(frame, self.current_fps, dets)
                cv2.imshow("LUNAR", frame)

            if cv2.waitKey(1) == ord('q'):
                self.running = False
                break

    def start(self):
        """Start all threads"""
        _debug_log("aimbot.py:start", "aimbot_start", {"roi_size": self.roi_size}, "run")
        self.running = True

        # Start C++ aim loop (outputs to queue; Python sends via Interception with batching)
        DLL.AimbotStartAimLoop(self.engine)
        print(colored("[+] C++ Aim Loop: STARTED (144Hz)", "cyan"))

        threading.Thread(target=self.mouse_output_loop, daemon=True).start()
        print(colored("[+] Mouse Output (Interception, batched): STARTED", "cyan"))

        # Start Python detection thread
        threading.Thread(target=self.detection_loop, daemon=True).start()
        print(colored("[+] Python Detection Loop: STARTED", "cyan"))

        # Display loop (main thread or sleep)
        if not Aimbot.config.get("headless", False):
            self.display_loop()
        else:
            while self.running:
                if not DLL.AimbotIsRunning(self.engine):
                    self.running = False
                    break
                time.sleep(1)

        # Cleanup
        DLL.AimbotStopAimLoop(self.engine)
        print(colored("[+] C++ Aimbot: STOPPED", "yellow"))


if __name__ == "__main__":
    print("Run gui.py")