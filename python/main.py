import time
import os
import sys
import dxcam
import cv2
import json
import ctypes
import threading
import math
from shared_mem import SharedMemoryManager

# Force unbuffered stdout
os.environ['PYTHONUNBUFFERED'] = '1'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from lib.model_loader import get_model_loader
# Bypass slow MouseController wrapper
# from lib.mouse_controller import get_controller

import win32api
import win32con
import win32gui

# Direct Interception Import
try:
    import interception
    # USE_INTERCEPTION = True
    USE_INTERCEPTION = False # Python doesn't need it, C++ has it.
    print("[+] Hybrid Mode: C++ Executor handles Interception")
except ImportError:
    print("[!] Interception Wrapper not found (OK for Hybrid Mode).")
    USE_INTERCEPTION = False

class HybridOrchestrator:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(base_dir, "lib", "config", "config.json")
        self.load_config()
        
        try:
            # FORCE DPI AWARENESS to get Native Resolution (Fix Init Overshoot)
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except: 
                ctypes.windll.user32.SetProcessDPIAware()
                
            self.screen_w = ctypes.windll.user32.GetSystemMetrics(0)
            self.screen_h = ctypes.windll.user32.GetSystemMetrics(1)
            print(f"[+] Screen Resolution Detected: {self.screen_w}x{self.screen_h}")
        except:
            self.screen_w = 1920
            self.screen_h = 1080

        self.camera = dxcam.create(output_color="BGR")
        
        self.model_loader = get_model_loader()
        if not self.model_loader.load():
            sys.exit(1)
            
        # self.mouse = get_controller(self.config) # REMOVED overhead
        self.shm = SharedMemoryManager()
        self.running = True
        
        # Velocity State
        self.current_vx = 0.0
        self.current_vy = 0.0
        self.last_ex = 0.0
        self.last_ey = 0.0
        self.acc_x = 0.0
        self.acc_y = 0.0
        
        # Hotkey State (MUST be in __init__, NOT in any loop)
        self.enabled = self.config.get("enabled", True)
        self.toggle_key = win32con.VK_F1
        self.exit_key = win32con.VK_F2
        self.last_toggle_time = 0
        self.is_aiming = False
        
        # Focus tracking: only aim when game window is active
        self.game_hwnd = None  # Will be set on first RMB hold
        
        print("[+] Python Orchestrator Initialized.")
        try:
            import psutil
            p = psutil.Process()
            p.nice(psutil.HIGH_PRIORITY_CLASS)
        except: pass
        
        # Force 1ms Timer Resolution (Crucial for 144Hz loops)
        try:
            self.winmm = ctypes.windll.winmm
            self.winmm.timeBeginPeriod(1)
            print("[+] System Timer Resolution set to 1ms")
        except: 
            print("[!] Failed to set Timer Resolution")

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            self.last_config_mtime = os.path.getmtime(self.config_path)
        except:
            self.config = {"roi_size": 320, "conf_thres": 0.45, "smoothing": 3.0, "x_speed": 280.0, "y_speed": 1.0}
            self.last_config_mtime = 0

    def get_roi(self):
        roi_size = self.config.get("roi_size", 320)
        left = (self.screen_w - roi_size) // 2
        top = (self.screen_h - roi_size) // 2
        return (left, top, left + roi_size, top + roi_size)

    def display_loop(self):
        while self.running:
            if hasattr(self, 'latest_frame') and self.latest_frame is not None:
                frame = self.latest_frame.copy()
                dets = getattr(self, 'latest_dets', [])
                best_center = getattr(self, 'latest_best_center', None)
                try:
                    if dets:
                        for det in dets:
                            x1, y1, x2, y2, conf = det
                            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    if best_center:
                        roi_size = self.config.get("roi_size", 320)
                        cv2.circle(frame, (int(best_center[0] + roi_size/2), int(best_center[1] + roi_size/2)), 4, (0, 0, 255), -1)
                        
                    # DRAW FOV CIRCLE:
                    fov_radius = int(self.config.get("fov_radius", 100))
                    roi_size = self.config.get("roi_size", 320)
                    center_x = int(roi_size / 2)
                    center_y = int(roi_size / 2)
                    cv2.circle(frame, (center_x, center_y), fov_radius, (255, 255, 255), 1) # White Circle

                    fps = getattr(self, 'fps_val', 0)
                    aiming = getattr(self, 'is_aiming', False)
                    enabled = getattr(self, 'enabled', True)
                    if not enabled:
                        status = "DISABLED"
                        color = (128, 128, 128)
                    elif aiming:
                        status = "AIMING"
                        color = (0, 0, 255)
                    else:
                        status = "IDLE" 
                        color = (0, 255, 0)
                    cv2.putText(frame, f"FPS: {fps} | {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    cv2.imshow("Lunar Overlay", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.stop()
                        break
                except: pass
            time.sleep(0.016)

    def check_hotkeys(self):
        # Toggle (F1)
        if win32api.GetAsyncKeyState(self.toggle_key) & 0x8000:
            if time.time() - self.last_toggle_time > 0.3: # Debounce
                self.enabled = not self.enabled
                print(f"[!] Aimbot {'ENABLED' if self.enabled else 'DISABLED'}")
                try:
                    import winsound
                    freq = 1000 if self.enabled else 500
                    winsound.Beep(freq, 200)
                except: pass
                self.last_toggle_time = time.time()
        
        # Exit (F2)
        if win32api.GetAsyncKeyState(self.exit_key) & 0x8000:
            print("[!] Exit Hotkey Pressed")
            self.stop()
            sys.exit(0)

    def run_mouse_logic(self, target_dx, target_dy, has_target):
        self.check_hotkeys()
        
        if not self.enabled:
            # Tell C++ to stop aiming
            self.shm.write_data(0, 0, False, 0.0, 0.0, False, 0.0, 0.0, 100, False)
            self.is_aiming = False
            return

        right_held = win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000
        self.is_aiming = bool(right_held)
        
        # Focus Check: Only aim when game window is in foreground
        if not self.enabled:
            # Tell C++ to stop aiming
            self.shm.write_data(0, 0, False, 0.0, 0.0, False, 0.0, 0.0, 100, False)
            self.is_aiming = False
            return

        right_held = win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000
        self.is_aiming = bool(right_held)
        
        # REMOVED WINDOW LOCKING: It was locking onto Desktop/Chrome if user tested there first.
        # Now we just trust RMB hold.
        
        ix, iy = 0, 0
        
        # MIGRATION: Python acts as SENSOR ONLY.
        # We send the RAW target distance to C++.
        # C++ handles Smoothing & Trajectory (1000Hz).
        
        if has_target and right_held:
            # Send Target Distance directly
            ix = int(target_dx)
            iy = int(target_dy)
        else:
            ix = 0
            iy = 0

        # Hybrid v3.1: Send Sensor Data to C++ Executor via Shared Memory
        # raw_input=False -> Tells C++ to use its own Smoothing Logic
        smoothing = float(self.config.get("smoothing", 3.0))
        humanization = float(self.config.get("humanization", 1.5))
        rcs_active = bool(self.config.get("rcs_enabled", False))
        rcs_x = float(self.config.get("rcs_strength_x", 0.0))
        rcs_x = float(self.config.get("rcs_strength_x", 0.0))
        rcs_y = float(self.config.get("rcs_strength_y", 0.0))
        
        self.shm.write_data(
            ix, iy, 
            has_target and bool(right_held),
            smoothing, humanization, rcs_active, rcs_x, rcs_y,
            int(self.config.get("fov_radius", 100)),
            raw_input=False,
            shutdown=False
        )
        
        # Debug: store last SHM values for console output
        if has_target and right_held:
            self._dbg_shm = f"| SHM: ({ix},{iy}) sm={smoothing:.1f}"

    def detection_loop(self):
        roi = self.get_roi()
        roi_size = self.config.get("roi_size", 320)
        
        if not self.camera.is_capturing:
            try:
                # target_fps=0 -> NATIVE SYNC (captures at monitor refresh rate)
                # This minimizes latency and tearing by syncing with DWM.
                self.camera.start(target_fps=0, video_mode=True, region=roi)
            except: pass 
            
        print("[+] Detection Thread Started (NATIVE SYNC)")
        
        frame_cnt = 0
        self.fps_val = 0
        start_t = time.perf_counter()
        self.last_frame_time = time.perf_counter()
        last_frame_obj = None
        
        last_config_check = time.perf_counter()
        
        while self.running:
            # Config Reload (Independent Timer)
            if time.perf_counter() - last_config_check > 0.5: # Check every 0.5s for responsiveness
                last_config_check = time.perf_counter()
                try: 
                    if os.path.exists(self.config_path):
                        self.load_config()
                        fov = self.config.get("fov_radius", 0)
                        sm = self.config.get("smoothing", 0)
                        print(f"[DBG] Config Sync: FOV={fov} Smooth={sm:.2f}") 
                except: pass

            frame = self.camera.get_latest_frame()
            if frame is None: 
                continue
            
            # CRITICAL: Prevent processing duplicate frames (dxcam returns same object if no new frame)
            # This prevents C++ interpolation resets and wasted YOLO inference.
            if frame is last_frame_obj:
                time.sleep(0.001) # Prevent 100% CPU spin
                # Watchdog: If stuck for > 0.5s, restart camera
                if time.perf_counter() - self.last_frame_time > 0.5:
                     print("[!] Frame Stuck - Restarting Camera...")
                     try:
                         self.camera.stop()
                         time.sleep(0.05)
                         self.camera.start(target_fps=0, video_mode=True, region=roi)
                         self.last_frame_time = time.perf_counter()
                     except: pass
                continue
            
            self.last_frame_time = time.perf_counter()
            last_frame_obj = frame
            
            # YOLO Inference
            dets = self.model_loader.infer(frame, self.config.get("conf_thres", 0.45))
            
            best_target_delta = None
            has_target = False
            
            if dets:
                center = roi_size / 2
                best_det = None
                min_dist = float('inf')
                fov = self.config.get("fov_radius", 100)
                
                for det in dets:
                    x1, y1, x2, y2, conf = det
                    bx, by = (x1 + x2) / 2, (y1 + y2) / 2
                    target_y = y1 + (y2 - y1) * self.config.get("aim_point_ratio", 0.2)
                    dist = ((bx - center)**2 + (by - center)**2)**0.5
                    
                    if dist < min_dist and dist < fov:
                        min_dist = dist
                        best_det = (bx - center, target_y - center)
                
                if best_det:
                    best_target_delta = (best_det[0], best_det[1])
                    has_target = True

            # Calculate movement (Python Math)
            if has_target:
                self.run_mouse_logic(best_target_delta[0], best_target_delta[1], True)
            else:
                self.run_mouse_logic(0, 0, False)
            
            # Update Latest Data for Display Thread
            if not self.config.get("headless", False):
                self.latest_frame = frame
                self.latest_dets = dets
                self.latest_best_center = (roi_size/2 + best_target_delta[0], roi_size/2 + best_target_delta[1]) if best_target_delta else None

            frame_cnt += 1
            if time.perf_counter() - start_t >= 1.0:
                self.fps_val = frame_cnt
                aim_str = 'ACTIVE' if getattr(self, 'is_aiming', False) else 'IDLE'
                en_str = 'ON' if self.enabled else 'OFF'
                dbg = getattr(self, '_dbg_shm', '')
                print(f"FPS: {frame_cnt} | AIM: {aim_str} | EN: {en_str} {dbg}")
                frame_cnt = 0
                start_t = time.perf_counter()

    def run(self):
        print("[+] Starting Hybrid V3 Orchestrator...")
        print("[+] Hold RIGHT MOUSE BUTTON to aim.")
        
        # Start Detection in separate thread
        t = threading.Thread(target=self.detection_loop, daemon=True)
        t.start()
        
        # Run Display in Main Thread (Better for CV2/Windows UI)
        if not self.config.get("headless", False):
            self.display_loop()
        else:
            # Just keep main thread alive
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        self.running = False
        if hasattr(self, 'camera') and self.camera.is_capturing:
            self.camera.stop()
        cv2.destroyAllWindows()
        if hasattr(self, 'shm'):
            self.shm.close()
        try:
             import ctypes
             ctypes.windll.winmm.timeEndPeriod(1)
        except: pass

if __name__ == "__main__":
    orch = HybridOrchestrator()
    try:
        orch.run()
    except KeyboardInterrupt:
        orch.stop()
