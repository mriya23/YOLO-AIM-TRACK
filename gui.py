"""
Lunar Aimbot GUI - SKECH Edition
Features:
- "SKECH" Inspired Layout (Sidebar + Cards)
- Crimson Red Theme
- Procedurally Generated Icons
- Real-time Config Tuning
"""
import customtkinter as ctk
import json
import os
import sys
import subprocess
import ctypes
from PIL import Image

try:
    from lib.ui_assets import AssetFactory
except ImportError:
    print("[!] AssetFactory not found. Icons will be disabled.")
    AssetFactory = None

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# Verbose Log for GUI Diagnostics
def gui_log(msg):
    try:
        with open("gui_debug.log", "a") as f:
            f.write(f"[{os.getpid()}] {msg}\n")
    except: pass
    print(msg)

gui_log("=== GUI STARTED ===")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# THEME CONSTANTS - SKECH PALETTE
COLOR_BG = "#111111"       # Deep Grey/Black
COLOR_SIDEBAR = "#0a0a0a"  # Darker Side
COLOR_CARD = "#1a1a1a"     # Card Background
COLOR_ACCENT = "#ff3333"   # Crimson Red
COLOR_TEXT = "#eeeeee"
COLOR_TEXT_DIM = "#888888"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue") # We will override specific colors

class LunarGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("LUNAR [SKECH EDITION]")
        self.geometry("850x600")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_dir = os.path.join(base_dir, "lib", "config")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.load_config()
        
        self.proc_cpp = None
        self.proc_py = None
        self.running = False
        self._slider_registry = {} 
        self.active_page = None
        
        # Load Assets
        self.assets = {}
        if AssetFactory:
            self.assets['logo'] = AssetFactory.get_logo((40, 40))
            self.assets['aim'] = AssetFactory.get_icon_aim((20, 20))
            self.assets['recoil'] = AssetFactory.get_icon_recoil((20, 20))
            self.assets['settings'] = AssetFactory.get_icon_settings((20, 20))

        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_layout(self):
        # 1. Sidebar (Left)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo Area
        logo_frame = ctk.CTkFrame(self.sidebar, height=80, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(20, 10))
        if self.assets.get('logo'):
            ctk.CTkLabel(logo_frame, image=self.assets['logo'], text="").pack()
        ctk.CTkLabel(logo_frame, text="LUNAR PROJECT", font=("Impact", 18), text_color=COLOR_ACCENT).pack(pady=5)

        # Navigation Buttons
        self.nav_buttons = []
        self._create_sidebar_btn("Combat", self.assets.get('aim'), lambda: self._show_page("combat"))
        self._create_sidebar_btn("Visuals", None, lambda: self._show_page("visuals")) # Placeholder
        self._create_sidebar_btn("Settings", self.assets.get('settings'), lambda: self._show_page("settings"))

        # Status Footer in Sidebar
        self.status_label = ctk.CTkLabel(self.sidebar, text="OFFLINE", text_color="#555555", font=("Consolas", 10, "bold"))
        self.status_label.pack(side="bottom", pady=20)

        # 2. Content Area (Right)
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_BG)
        self.content.pack(side="right", fill="both", expand=True)

        # Pages
        self.pages = {
            "combat": self._build_page_combat(),
            "visuals": self._build_page_visuals(),
            "settings": self._build_page_settings()
        }
        
        self._show_page("combat")

    def _create_sidebar_btn(self, text, icon, command):
        btn = ctk.CTkButton(self.sidebar, text=f"  {text}", image=icon, 
                            compound="left", anchor="w", height=40,
                            fg_color="transparent", hover_color="#222222",
                            text_color=COLOR_TEXT, font=("Roboto", 12, "bold"),
                            command=lambda: [self._update_nav_state(btn), command()])
        btn.pack(fill="x", padx=10, pady=2)
        self.nav_buttons.append(btn)
        return btn

    def _update_nav_state(self, active_btn):
        for btn in self.nav_buttons:
            btn.configure(fg_color="transparent", text_color=COLOR_TEXT)
            # Remove left border indicator logic for simplicity or add later
        active_btn.configure(fg_color="#1a1a1a", text_color=COLOR_ACCENT)

    def _show_page(self, name):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[name].pack(fill="both", expand=True, padx=20, pady=20)

    # === PAGES ===
    def _build_page_combat(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        
        # COLUMN 1: Aimbot
        col1 = ctk.CTkFrame(page, fg_color="transparent")
        col1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Aimbot Card
        card_aim = self._create_card(col1, "Aimbot", "aimbot_enabled")
        self._create_slider(card_aim, "Field of View", "fov_radius", 50, 600, 150)
        self._create_slider(card_aim, "Smooth", "smoothing", 1.0, 40.0, 5.0)
        self._create_slider(card_aim, "Aim Distance (X Speed)", "speed_x", 1.0, 500.0, 250.0)
        
        # Misc Card (Bone)
        card_misc = self._create_card(col1, "Targeting", None)
        self._create_slider(card_misc, "Height Ratio (Head-Chest)", "aim_point_ratio", 0.0, 0.5, 0.2)
        self._create_slider(card_misc, "Confidence", "conf_thres", 0.1, 0.9, 0.45)

        # COLUMN 2: Recoil & Trigger
        col2 = ctk.CTkFrame(page, fg_color="transparent")
        col2.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # RCS Card
        card_rcs = self._create_card(col2, "Recoil Control System", "rcs_enabled")
        self._create_slider(card_rcs, "RCS Strength X", "rcs_strength_x", 0.0, 10.0, 0.5)
        self._create_slider(card_rcs, "RCS Strength Y", "rcs_strength_y", 0.0, 10.0, 2.0)
        
        # Triggerbot Card (Placeholder for visual completeness)
        card_trig = self._create_card(col2, "Alternative Input", None)
        self._create_checkbox(card_trig, "Software Mouse (No Executor)", "software_mouse")
        self._create_checkbox(card_trig, "Trigger on Head Only", "trigger_head")
        
        return page

    def _build_page_visuals(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        ctk.CTkLabel(page, text="VISUALS COMING SOON", text_color=COLOR_TEXT_DIM).pack(expand=True)
        return page

    def _build_page_settings(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        
        # Config Card
        card_cfg = self._create_card(page, "Configuration", None)

        # Hotkeys
        hk_frame = ctk.CTkFrame(card_cfg, fg_color="transparent")
        hk_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(hk_frame, text="Toggle Key", text_color=COLOR_TEXT_DIM).pack(side="left", padx=10)
        self.hotkey_toggle = ctk.CTkEntry(hk_frame, width=80, fg_color="#222", border_color="#333", text_color=COLOR_ACCENT)
        self.hotkey_toggle.insert(0, self.config.get("hotkey_toggle", "F1"))
        self.hotkey_toggle.pack(side="right", padx=10)
        
        hk_frame2 = ctk.CTkFrame(card_cfg, fg_color="transparent")
        hk_frame2.pack(fill="x", pady=10)
        
        ctk.CTkLabel(hk_frame2, text="Panic Key", text_color=COLOR_TEXT_DIM).pack(side="left", padx=10)
        self.hotkey_exit = ctk.CTkEntry(hk_frame2, width=80, fg_color="#222", border_color="#333", text_color="#ff5555")
        self.hotkey_exit.insert(0, self.config.get("hotkey_exit", "F2"))
        self.hotkey_exit.pack(side="right", padx=10)
        
        ctk.CTkButton(card_cfg, text="SAVE CONFIG", fg_color=COLOR_ACCENT, hover_color="#cc0000", 
                      command=self.save_config).pack(fill="x", pady=20, padx=20)
        
        # Actions
        card_act = self._create_card(page, "Engine State", None)
        self.btn_start = ctk.CTkButton(card_act, text="ENABLE ENGINE", command=self._on_start,
                                       fg_color="#222", hover_color="#333", border_width=1, border_color=COLOR_ACCENT,
                                       text_color=COLOR_ACCENT)
        self.btn_start.pack(fill="x", pady=10, padx=20)
        
        self.btn_stop = ctk.CTkButton(card_act, text="DISABLE ENGINE", command=self._on_stop,
                                       fg_color="#222", hover_color="#333", state="disabled")
        self.btn_stop.pack(fill="x", pady=10, padx=20)
        
        return page

    # === WIDGETS ===
    def _create_card(self, parent, title, toggle_key=None):
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=6, border_width=1, border_color="#222")
        card.pack(fill="x", pady=(0, 15))
        
        # Header
        header = ctk.CTkFrame(card, height=35, fg_color="#222", corner_radius=6)
        header.pack(fill="x", padx=1, pady=1)
        
        # Red Accent Line
        ctk.CTkFrame(header, width=3, height=20, fg_color=COLOR_ACCENT).pack(side="left", padx=10, pady=8)
        
        ctk.CTkLabel(header, text=title, font=("Roboto", 12, "bold"), text_color=COLOR_TEXT).pack(side="left")
        
        if toggle_key:
            switch = ctk.CTkSwitch(header, text="", width=40, height=20, 
                                   progress_color=COLOR_ACCENT, button_color="#FFF",
                                   command=lambda k=toggle_key: self._toggle_config(k))
            switch.pack(side="right", padx=10)
            if self.config.get(toggle_key, True): switch.select()
            
        return card

    def _create_slider(self, parent, label, key, min_v, max_v, default):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=8)
        
        # Label Row
        l_frame = ctk.CTkFrame(frame, fg_color="transparent")
        l_frame.pack(fill="x")
        ctk.CTkLabel(l_frame, text=label, text_color=COLOR_TEXT_DIM, font=("Roboto", 11)).pack(side="left")
        
        val_label = ctk.CTkLabel(l_frame, text="0.0", text_color=COLOR_TEXT, font=("Consolas", 11))
        val_label.pack(side="right")
        
        # Slim Slider
        slider = ctk.CTkSlider(frame, from_=min_v, to=max_v, number_of_steps=100,
                               progress_color=COLOR_ACCENT, button_color=COLOR_ACCENT, button_hover_color="#fff",
                               fg_color="#333", height=10, border_width=0,
                               command=lambda v, k=key, l=val_label: self._on_slider(v, k, l))
        slider.pack(fill="x", pady=(5, 0))
        
        val = float(self.config.get(key, default))
        slider.set(val)
        val_label.configure(text=f"{val:.2f}")

    def _create_checkbox(self, parent, label, key):
        cb = ctk.CTkCheckBox(parent, text=label, text_color=COLOR_TEXT_DIM,
                             fg_color=COLOR_ACCENT, hover_color="#cc0000",
                             font=("Roboto", 11),
                             command=lambda: self._toggle_config(key))
        cb.pack(anchor="w", padx=15, pady=5)
        if self.config.get(key, False):
            cb.select()

    # === LOGIC ===
    def _on_slider(self, val, key, label):
        self.config[key] = float(val)
        label.configure(text=f"{float(val):.2f}")
        self._debounce_save()

    def _toggle_config(self, key):
        self.config[key] = not self.config.get(key, False)
        self.save_config()

    def _debounce_save(self):
        if hasattr(self, "_save_timer"): self.after_cancel(self._save_timer)
        self._save_timer = self.after(500, self.save_config)

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f: self.config = json.load(f)
        except:
            self.config = {"speed_x": 250, "rcs_enabled": True} # Minimal defaults
    
    def save_config(self):
        if hasattr(self, 'hotkey_toggle'):
            self.config["hotkey_toggle"] = self.hotkey_toggle.get()
            self.config["hotkey_exit"] = self.hotkey_exit.get()
        with open(self.config_file, 'w') as f: json.dump(self.config, f, indent=4)

    def _on_start(self):
        if self.running: return
        gui_log("=== STARTING ENGINE FLOW ===")
        self.status_label.configure(text="INITIALIZING...", text_color="#FF8800")
        
        # Bersihkan sisa EXECUTOR lama saja (Python jangan di-kill masal)
        try:
            gui_log("Cleaning old executor instances...")
            subprocess.run(["taskkill", "/F", "/IM", "executor.exe", "/T"], capture_output=True)
        except: pass

        # Paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        py_main = os.path.join(script_dir, "python", "main.py")
        exe_path = os.path.join(script_dir, "cpp", "executor.exe")
        exe_dir = os.path.dirname(exe_path)
        
        # 1. Launch Python Backend
        gui_log(f"Launching Python Backend: {py_main}")
        try:
            # Gunakan window baru secara langsung (lebih stabil dibanding pipa log)
            self.proc_py = subprocess.Popen(
                [sys.executable, py_main], 
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            gui_log(f"Python Backend success (PID: {self.proc_py.pid})")
        except Exception as e:
            gui_log(f"CRITICAL: Python failed: {e}")
            self.status_label.configure(text="❌ PY START FAILED", text_color="#ff0000")
            return

        # 2. Launch Executor
        self.status_label.configure(text="LAUNCHING C++...", text_color="#FFFF00")
        self.after(2000, lambda: self._final_launch(exe_path, exe_dir))

    def _final_launch(self, exe_path, exe_dir):
        gui_log(f"Attempting Final launch: {exe_path}")
        if os.path.exists(exe_path):
             try:
                 # Tanpa pipa log agar stabil
                 self.proc_cpp = subprocess.Popen(
                     [exe_path], 
                     cwd=exe_dir, 
                     creationflags=subprocess.CREATE_NEW_CONSOLE
                 )
                 gui_log(f"Executor success (PID: {self.proc_cpp.pid})")
                 self.status_label.configure(text="● SYSTEM ONLINE", text_color="#00ff88")
                 self.running = True
                 self.btn_start.configure(state="disabled", fg_color="#111", text_color="#333")
                 self.btn_stop.configure(state="normal", fg_color="#330000", text_color="#ff5555")
             except Exception as e:
                 gui_log(f"CRITICAL: Executor launch failed: {e}")
                 self.status_label.configure(text="❌ EXE LAUNCH ERROR", text_color="#ff0000")
        else:
             gui_log("ERROR: executor.exe NOT FOUND")
             self.status_label.configure(text="❌ EXE MISSING", text_color="#ff0000")

    def _on_stop(self):
        if self.proc_py: self.proc_py.terminate()
        if self.proc_cpp: self.proc_cpp.terminate()
        self.proc_py = None
        self.proc_cpp = None
        self.running = False
        self.status_label.configure(text="OFFLINE", text_color="#555")
        self.btn_start.configure(state="normal", fg_color="#222", text_color=COLOR_ACCENT)
        self.btn_stop.configure(state="disabled", fg_color="#111", text_color="#333")

    def on_close(self):
        self._on_stop()
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    LunarGUI().mainloop()