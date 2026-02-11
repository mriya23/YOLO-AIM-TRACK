"""
Lunar Aimbot GUI - Hybrid Launcher Edition
Features:
- Launches C++ Executor (Muscle) & Python Orchestrator (Brain)
- Real-time Config Tuning (Hot-Reload)
- Controls for Humanization & Dynamic RCS
"""
import customtkinter as ctk
import json
import os
import sys
import subprocess
import time
import psutil
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Re-run the program with admin rights
    print("[!] Requesting Admin Privileges...")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class LunarGUI(ctk.CTk):
    """Modern tabbed GUI for Lunar Aimbot Hybrid"""
    
    def __init__(self):
        super().__init__()
        
        self.title("🎯 LUNAR HYBRID CONTROL")
        self.geometry("540x550")
        self.resizable(False, False)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_dir = os.path.join(base_dir, "lib", "config")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.load_config()
        
        self.proc_cpp = None
        self.proc_py = None
        self.running = False
        
        # === ALT-TAB PROTECTION ===
        # CustomTkinter re-renders sliders on FocusIn, causing phantom value changes.
        # We suppress all saves during the cooldown period after regaining focus,
        # and reset sliders to their last known good values.
        self._suppress_saves = False
        self._slider_registry = {}  # key -> (slider_widget, [last_val])
        
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Bind FocusIn to reset sliders after alt-tab
        self.bind("<FocusIn>", self._on_focus_in)
    
    def _build_ui(self):
        """Build tabbed UI"""
        # Header
        header = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="🚀 LUNAR HYBRID", font=("Roboto", 22, "bold"),
                     text_color="#e94560").pack(side="left", padx=20, pady=10)
        
        self.status_label = ctk.CTkLabel(header, text="● READY",
                                         text_color="#00ff88", font=("Roboto", 12, "bold"))
        self.status_label.pack(side="right", padx=20)
        
        # Tabview
        self.tabview = ctk.CTkTabview(self, fg_color="#0f0f1a")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create tabs
        self.tab_aim = self.tabview.add("🎯 Aim")
        self.tab_recoil = self.tabview.add("🔫 Recoil")
        self.tab_advanced = self.tabview.add("⚙️ Advanced")
        
        self._build_aim_tab()
        self._build_recoil_tab()
        self._build_advanced_tab()
        
        # Bottom buttons
        self._build_buttons()
    
    def _build_aim_tab(self):
        """Aim, Smoothing & Humanization"""
        frame = self.tab_aim
        
        # Toggles row
        toggle_frame = ctk.CTkFrame(frame, fg_color="#16213e", corner_radius=10)
        toggle_frame.pack(fill="x", pady=5, padx=5)
        
        self.switch_headless = ctk.CTkSwitch(toggle_frame, text="HEADLESS (No Overlay)",
                                             command=self._on_headless_toggle,
                                             progress_color="#e94560")
        self.switch_headless.pack(side="left", padx=15, pady=10)
        if self.config.get("headless", False):
            self.switch_headless.select()
        
        # Aim Settings
        settings = ctk.CTkFrame(frame, fg_color="#16213e", corner_radius=10)
        settings.pack(fill="both", expand=True, pady=5, padx=5)
        
        self._create_slider(settings, "FOV Radius", "fov_radius", 10, 500, int)
        self._create_slider(settings, "Smoothing", "smoothing", 0.05, 50.0, float)
        
        ctk.CTkLabel(settings, text="HUMANIZATION (Anti-Cheat)", font=("Roboto", 11, "bold"),
                     text_color="#e94560").pack(anchor="w", padx=10, pady=(15, 5))
        self._create_slider(settings, "Jitter (px)", "humanization", 0.0, 5.0, float)
        
        # Bone preset
        bone_frame = ctk.CTkFrame(settings, fg_color="transparent")
        bone_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(bone_frame, text="Target Bone", width=100, anchor="w").pack(side="left")
        self.bone_option = ctk.CTkOptionMenu(bone_frame, values=["Head", "Neck", "Chest"],
                                             command=self._on_bone_change,
                                             fg_color="#e94560", button_color="#c73e54")
        self.bone_option.pack(side="left", expand=True, fill="x", padx=10)
        self._set_bone_from_config()
    
    def _build_recoil_tab(self):
        """Dynamic RCS settings"""
        frame = self.tab_recoil
        
        toggle_frame = ctk.CTkFrame(frame, fg_color="#16213e", corner_radius=10)
        toggle_frame.pack(fill="x", pady=5, padx=5)
        
        self.switch_rcs = ctk.CTkSwitch(toggle_frame, text="ENABLE RCS",
                                        command=self._on_rcs_toggle,
                                        progress_color="#e94560")
        self.switch_rcs.pack(side="left", padx=15, pady=10)
        if self.config.get("rcs_enabled", True):
            self.switch_rcs.select()
            
        settings = ctk.CTkFrame(frame, fg_color="#16213e", corner_radius=10)
        settings.pack(fill="both", expand=True, pady=5, padx=5)
        
        ctk.CTkLabel(settings, text="RECOIL CONTROL STRENGTH", font=("Roboto", 11, "bold"),
                     text_color="#e94560").pack(anchor="w", padx=10, pady=5)
                     
        self._create_slider(settings, "Vert (Pull Down)", "rcs_strength_y", 0.0, 10.0, float)
        self._create_slider(settings, "Horz (Anti-Sway)", "rcs_strength_x", 0.0, 5.0, float)
        
        ctk.CTkLabel(settings, text="*Adjust while shooting at a wall to tune*", 
                    font=("Roboto", 10, "italic"), text_color="#aaa").pack(pady=10)

    def _build_advanced_tab(self):
        """Advanced settings"""
        frame = self.tab_advanced
        
        settings = ctk.CTkFrame(frame, fg_color="#16213e", corner_radius=10)
        settings.pack(fill="both", expand=True, pady=5, padx=5)
        
        ctk.CTkLabel(settings, text="DETECTION", font=("Roboto", 11, "bold"),
                     text_color="#e94560").pack(anchor="w", padx=10, pady=5)
        self._create_slider(settings, "Confidence", "conf_thres", 0.1, 0.9, float)
        self._create_slider(settings, "ROI Size", "roi_size", 100, 800, int)
        
        ctk.CTkLabel(settings, text="HOTKEYS", font=("Roboto", 11, "bold"),
                     text_color="#e94560").pack(anchor="w", padx=10, pady=(15, 5))
        
        hk_frame = ctk.CTkFrame(settings, fg_color="transparent")
        hk_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(hk_frame, text="Toggle:", width=60, anchor="w").pack(side="left")
        self.hotkey_toggle = ctk.CTkEntry(hk_frame, width=60)
        self.hotkey_toggle.insert(0, self.config.get("hotkey_toggle", "F1"))
        self.hotkey_toggle.pack(side="left", padx=5)
        
        ctk.CTkLabel(hk_frame, text="Exit:", width=40, anchor="w").pack(side="left", padx=(10,0))
        self.hotkey_exit = ctk.CTkEntry(hk_frame, width=60)
        self.hotkey_exit.insert(0, self.config.get("hotkey_exit", "F2"))
        self.hotkey_exit.pack(side="left", padx=5)
    
    def _build_buttons(self):
        """Action buttons"""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_start = ctk.CTkButton(btn_frame, text="▶ START ENGINE", command=self._on_start,
                                       fg_color="#e94560", hover_color="#c73e54",
                                       height=45, font=("Roboto", 14, "bold"))
        self.btn_start.pack(side="left", expand=True, fill="x", padx=5)
        
        self.btn_stop = ctk.CTkButton(btn_frame, text="⏹ STOP", command=self._on_stop,
                                      fg_color="#333", hover_color="#555",
                                      height=45, font=("Roboto", 14, "bold"), state="disabled")
        self.btn_stop.pack(side="left", expand=True, fill="x", padx=5)
    
    # === HELPERS ===
    
    def _create_slider(self, parent, label, key, min_v, max_v, vtype, scale=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(frame, text=label, width=120, anchor="w").pack(side="left")
        
        current = self.config.get(key, min_v)
        fmt = "{:.0f}" if (vtype == int or scale != 1) else "{:.2f}"
        
        val_label = ctk.CTkLabel(frame, text=fmt.format(current * scale), width=40)
        val_label.pack(side="right")
        
        def on_drag(v):
            # Update label
            val_label.configure(text=fmt.format(vtype(v) * scale))
            
            # Update config in memory
            val = vtype(v)
            self.config[key] = val
            
            # TRIGGER DEBOUNCED SAVE (0.5s delay)
            if hasattr(self, f"_save_timer_{key}"):
                self.after_cancel(getattr(self, f"_save_timer_{key}"))
            
            # Schedule save
            timer_id = self.after(500, self.save_config)
            setattr(self, f"_save_timer_{key}", timer_id)
        
        slider = ctk.CTkSlider(frame, from_=min_v, to=max_v, command=on_drag,
                               progress_color="#e94560", button_color="#e94560")
        slider.pack(side="left", expand=True, fill="x", padx=10)
        slider.set(current)
        
        # Register for focus-reset
        self._slider_registry[key] = (slider, [current])
    
    def _on_focus_in(self, event):
        """Reset slider positions to match current config (cosmetic fix only)."""
        for key, (slider, last_val) in self._slider_registry.items():
            try:
                config_val = self.config.get(key, last_val[0])
                slider.set(config_val)
                last_val[0] = config_val
            except: pass
    
    def _set_bone_from_config(self):
        r = self.config.get("aim_point_ratio", 0.12)
        self.bone_option.set("Head" if r <= 0.15 else "Neck" if r <= 0.25 else "Chest")
    
    # === CALLBACKS ===
    
    def load_config(self):
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {
                "enabled": True, "headless": False, "roi_size": 320, 
                "conf_thres": 0.45, "smoothing": 0.2, "humanization": 1.5,
                "rcs_enabled": True, "rcs_strength_x": 0.5, "rcs_strength_y": 2.0,
                "fov_radius": 100
            }
            self.save_config()
    
    def save_config(self):
        try:
            self.config["hotkey_toggle"] = self.hotkey_toggle.get()
            self.config["hotkey_exit"] = self.hotkey_exit.get()
        except: pass
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Save error: {e}")
    
    def _on_bone_change(self, choice):
        self.config["aim_point_ratio"] = {"Head": 0.12, "Neck": 0.20, "Chest": 0.30}[choice]
        self.save_config()
        
    def _on_headless_toggle(self):
        self.config["headless"] = bool(self.switch_headless.get())
        self.save_config()
        
    def _on_rcs_toggle(self):
        self.config["rcs_enabled"] = bool(self.switch_rcs.get())
        self.save_config()
    
    def _on_start(self):
        if self.running: return
        
        # Paths
        cpp_exe = os.path.join("cpp", "executor.exe")
        py_main = os.path.join("python", "main.py")
        
        if not os.path.exists(cpp_exe):
            self.status_label.configure(text="❌ ERR: Executor not found!", text_color="#ff0000")
            return
            
        try:
            # Launch Python Orchestrator FIRST (Creates Shared Memory)
            self.proc_py = subprocess.Popen(["python", py_main], creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # Wait for Python to create Shared Memory
            import time
            time.sleep(2)
            
            # Launch C++ Executor SECOND (Connects to Shared Memory)
            self.proc_cpp = subprocess.Popen([cpp_exe], creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            self.running = True
            self.status_label.configure(text="✅ HYBRID RUNNING", text_color="#00ff88")
            self.btn_start.configure(state="disabled", fg_color="#333")
            self.btn_stop.configure(state="normal", fg_color="#e94560")
            
        except Exception as e:
            print(e)
            self.status_label.configure(text=f"❌ ERR: {e}", text_color="#ff0000")
            self._on_stop()

    def _on_stop(self):
        if self.proc_py:
            self.proc_py.terminate()
            self.proc_py = None
        
        if self.proc_cpp:
            self.proc_cpp.terminate()
            self.proc_cpp = None
            
        self.running = False
        self.status_label.configure(text="● READY", text_color="#00ff88")
        self.btn_start.configure(state="normal", fg_color="#e94560")
        self.btn_stop.configure(state="disabled", fg_color="#333")
    
    def on_close(self):
        self._on_stop()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    LunarGUI().mainloop()