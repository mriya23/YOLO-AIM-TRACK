"""
Lunar Aimbot GUI - ImGui Edition (SKECH v4 Modern)
Features:
- "Material Dark" Aesthetic (Rounded, Matte, Soft)
- Segoe UI Typography (Windows Native)
- Floating Card Layout
- Full Feature Set
"""
import dearpygui.dearpygui as dpg
import json
import os
import sys
import subprocess
import ctypes
import threading

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "lib", "config", "config.json")

# MODERN PALETTE
C_BG = (18, 18, 18, 255)          # Google Material Dark
C_PANEL = (30, 30, 30, 255)       # Lighter Surface
C_ACCENT = (255, 110, 20, 255)    # Soft Orange
C_ACCENT_HOVER = (255, 140, 50, 255)
C_TEXT = (240, 240, 240, 255)     # High Contrast Text
C_TEXT_DIM = (140, 140, 140, 255)
C_BORDER = (45, 45, 45, 255)

class LunarImGui:
    def __init__(self):
        self.config = {}
        self.load_config()
        self.proc_py = None
        self.proc_cpp = None
        self.running = False
        self.setup_dpg()

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f: self.config = json.load(f)
        except: self.config = {}

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f, indent=4)
        except: pass

    def update_cfg(self, s, data, key):
        self.config[key] = data
        self.save_config()
        
    def update_bone(self, s, data, key):
        ratios = {"Head": 0.2, "Neck": 0.25, "Chest": 0.3}
        self.config["aim_point_ratio"] = ratios.get(data, 0.2)
        self.save_config()

    def toggle_engine(self):
        if self.running: self.stop_engine()
        else: self.start_engine()

    def start_engine(self):
        if self.running: return
        self.proc_py = subprocess.Popen(["python", os.path.join(BASE_DIR, "python", "main.py")], creationflags=subprocess.CREATE_NEW_CONSOLE)
        threading.Timer(2.0, self._launch_cpp).start()
        dpg.configure_item("status_sc", label="STARTING...", color=(255, 255, 0, 255))

    def _launch_cpp(self):
        exe = os.path.join(BASE_DIR, "cpp", "executor.exe")
        if os.path.exists(exe):
            self.proc_cpp = subprocess.Popen([exe], creationflags=subprocess.CREATE_NEW_CONSOLE)
            dpg.configure_item("status_sc", label="ONLINE", color=(0, 255, 100, 255))
            dpg.configure_item("btn_main", label="STOP ENGINE", user_data="stop")
            self.running = True

    def stop_engine(self):
        if self.proc_py: self.proc_py.terminate()
        if self.proc_cpp: self.proc_cpp.terminate()
        self.running = False
        dpg.configure_item("status_sc", label="OFFLINE", color=(100, 100, 100, 255))
        dpg.configure_item("btn_main", label="ENABLE CHEAT", user_data="start")

    def setup_theme(self):
        with dpg.theme() as t:
            with dpg.theme_component(dpg.mvAll):
                # Modern Rounding
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
                dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 12)
                
                # Spacing (Airy feel)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 12, 12)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 20, 20)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6)

                # Modern Palette
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, C_BG)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, C_PANEL)
                dpg.add_theme_color(dpg.mvThemeCol_Border, C_BORDER)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (40, 40, 40, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (50, 50, 50, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (60, 60, 60, 255))
                
                dpg.add_theme_color(dpg.mvThemeCol_CheckMark, C_ACCENT)
                
                # Slider (White Knob, Accent Rail)
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (240, 240, 240, 255))
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (255, 255, 255, 255))
                
                # Button (Subtle Surface)
                dpg.add_theme_color(dpg.mvThemeCol_Button, (45, 45, 45, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (60, 60, 60, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (70, 70, 70, 255))
                
                dpg.add_theme_color(dpg.mvThemeCol_Text, C_TEXT)
            
            # Specific Overrides
            with dpg.theme_component(dpg.mvSliderFloat):
                 dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, C_ACCENT)
                 dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, C_ACCENT_HOVER)

        dpg.bind_theme(t)

    def load_fonts(self):
        # Load Segoe UI (Windows Standard)
        font_path = "C:/Windows/Fonts/segoeui.ttf"
        font_bold = "C:/Windows/Fonts/segoeuib.ttf"
        
        with dpg.font_registry():
            try:
                # Main Font
                with dpg.font(font_path, 18) as self.font_main:
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                
                # Header Font
                with dpg.font(font_bold, 28) as self.font_header:
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                    
                # Small Header
                with dpg.font(font_bold, 20) as self.font_sub:
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                
                dpg.bind_font(self.font_main)
            except:
                print("Failed to load Segoe UI. Using default.")

    def setup_dpg(self):
        dpg.create_context()
        self.load_fonts()
        self.setup_theme()
        
        with dpg.window(tag="Main", no_title_bar=True, width=950, height=650):
            
            with dpg.group(horizontal=True):
                
                # === SIDEBAR (Modern Minimalist) ===
                with dpg.child_window(width=220, border=False):
                    dpg.add_spacer(height=20)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=20)
                        dpg.bind_item_font(dpg.add_text("LUNAR", color=C_ACCENT), self.font_header)
                        dpg.bind_item_font(dpg.add_text("PROJECT"), self.font_header)
                    
                    dpg.add_spacer(height=50)
                    
                    def nav_btn(label, icon="   ", tag=None):
                        b = dpg.add_button(label=f"  {icon}   {label}", width=180, height=50, tag=tag)
                        # No Logic here, wired later
                    
                    nav_btn("AIMBOT", "🎯", "btn_aim")
                    nav_btn("VISUALS", "👁", "btn_vis")
                    nav_btn("SETTINGS", "⚙", "btn_cfg")
                    
                    dpg.add_spacer(height=200)
                    
                    # Status Pill
                    with dpg.group(horizontal=True):
                         dpg.add_spacer(width=25)
                         dpg.add_text("SYSTEM STATUS", color=C_TEXT_DIM)
                    
                    dpg.add_text("       OFFLINE", tag="status_sc", color=(100, 100, 100, 255))
                    dpg.add_spacer(height=10)
                    
                    # Big Action Button
                    btn = dpg.add_button(label="ACTIVATE", tag="btn_main", width=180, height=55, callback=self.toggle_engine)
                    dpg.bind_item_font(btn, self.font_sub)

                dpg.add_spacer(width=15) 

                # === CONTENT AREA (Floating Card Look) ===
                with dpg.child_window(border=False):
                    dpg.add_spacer(height=15)
                    
                    # === PAGE: AIMBOT ===
                    with dpg.group(tag="group_aimbot"):
                        dpg.bind_item_font(dpg.add_text("Targeting Systems"), self.font_sub)
                        dpg.add_spacer(height=10)
                        
                        with dpg.group(horizontal=True):
                            # Left Card
                            with dpg.child_window(width=310, height=530, border=True):
                                dpg.add_text("Main Switches", color=C_ACCENT)
                                dpg.add_separator()
                                dpg.add_spacer(height=5)
                                
                                def cb(lbl, key):
                                    dpg.add_checkbox(label=lbl, default_value=self.config.get(key, True), 
                                                     callback=self.update_cfg, user_data=key)
                                
                                cb("Active Enable", "aimbot_enabled")
                                cb("Recoil Control", "rcs_enabled")
                                cb("Triggerbot", "trigger_enabled")
                                cb("Head Only Trigger", "trigger_head")
                                
                                dpg.add_spacer(height=20)
                                dpg.add_text("Bone Logic", color=C_ACCENT)
                                dpg.add_combo(("Head", "Neck", "Chest"), label="", default_value="Head", callback=self.update_bone, width=280)
                                
                                dpg.add_spacer(height=20)
                                dpg.add_text("Field of View (FOV)", color=C_ACCENT)
                                dpg.add_slider_float(label="", default_value=self.config.get("fov_radius", 150),
                                                     min_value=10, max_value=600, callback=self.update_cfg, user_data="fov_radius", width=280)
                                
                                dpg.add_spacer(height=10)
                                dpg.add_text("Confidence", color=C_ACCENT)
                                dpg.add_slider_float(label="", default_value=self.config.get("conf_thres", 0.45),
                                                     min_value=0.1, max_value=0.9, format="%.2f", callback=self.update_cfg, user_data="conf_thres", width=280)

                            dpg.add_spacer(width=15)

                            # Right Card
                            with dpg.child_window(width=310, height=530, border=True):
                                dpg.add_text("Humanization & Speed", color=C_ACCENT)
                                dpg.add_separator()
                                dpg.add_spacer(height=10)
                                
                                dpg.add_text("Smoothing")
                                dpg.add_slider_float(label="", default_value=self.config.get("smoothing", 5.0),
                                                     min_value=1.0, max_value=40.0, callback=self.update_cfg, user_data="smoothing", width=280)
                                
                                dpg.add_spacer(height=15)
                                dpg.add_text("Speed X (Horizontal)")
                                dpg.add_slider_float(label="", default_value=self.config.get("speed_x", 250.0),
                                                     min_value=1.0, max_value=500.0, callback=self.update_cfg, user_data="speed_x", width=280)

                                dpg.add_spacer(height=10)
                                dpg.add_text("Speed Y (Vertical)")
                                dpg.add_slider_float(label="", default_value=self.config.get("speed_y", 10.0),
                                                     min_value=1.0, max_value=100.0, callback=self.update_cfg, user_data="speed_y", width=280)

                                dpg.add_spacer(height=25)
                                dpg.add_text("RCS Strength")
                                dpg.add_slider_float(label=" X", default_value=self.config.get("rcs_strength_x", 0.5),
                                                     min_value=0.0, max_value=5.0, callback=self.update_cfg, user_data="rcs_strength_x", width=280)
                                dpg.add_slider_float(label=" Y", default_value=self.config.get("rcs_strength_y", 2.0),
                                                     min_value=0.0, max_value=5.0, callback=self.update_cfg, user_data="rcs_strength_y", width=280)

                    # === GROUP: VISUALS ===
                    with dpg.group(tag="group_visuals", show=False):
                         dpg.bind_item_font(dpg.add_text("Visual Settings"), self.font_sub)
                         dpg.add_spacer(height=10)
                         with dpg.child_window(width=635, height=530, border=True):
                             dpg.add_checkbox(label="Draw FOV Circle", default_value=self.config.get("draw_fov", False), 
                                              callback=self.update_cfg, user_data="draw_fov")
                             
                             dpg.add_spacer(height=20)
                             dpg.add_text("Overlay Color", color=C_ACCENT)
                             dpg.add_color_edit(label="", default_value=(255, 0, 0, 255), width=280, no_inputs=True)

                    # === GROUP: SETTINGS ===
                    with dpg.group(tag="group_cfg", show=False):
                        dpg.bind_item_font(dpg.add_text("System Configuration"), self.font_sub)
                        dpg.add_spacer(height=10)
                        
                        with dpg.child_window(width=635, height=530, border=True):
                            dpg.add_text("Input Bindings", color=C_ACCENT)
                            dpg.add_input_text(label=" Toggle Key", default_value=self.config.get("hotkey_toggle", "F1"), 
                                               callback=self.update_cfg, user_data="hotkey_toggle", width=150)
                            dpg.add_input_text(label=" Panic Key", default_value=self.config.get("hotkey_exit", "F2"), 
                                               callback=self.update_cfg, user_data="hotkey_exit", width=150)
                            
                            dpg.add_spacer(height=30)
                            dpg.add_checkbox(label="Headless Mode (Performance)", default_value=self.config.get("headless", False), 
                                             callback=self.update_cfg, user_data="headless")
                            
                            dpg.add_spacer(height=40)
                            dpg.add_button(label="FORCE SAVE CONFIG", callback=self.save_config, width=280, height=40)

        # NAV LOGIC
        def show_page(page_tag):
            dpg.configure_item("group_aimbot", show=False)
            dpg.configure_item("group_visuals", show=False)
            dpg.configure_item("group_cfg", show=False)
            dpg.configure_item(page_tag, show=True)

        dpg.configure_item("btn_aim", callback=lambda: show_page("group_aimbot"))
        dpg.configure_item("btn_vis", callback=lambda: show_page("group_visuals"))
        dpg.configure_item("btn_cfg", callback=lambda: show_page("group_cfg"))

        dpg.create_viewport(title='LUNAR [MODERN]', width=950, height=650, decorated=True, resizable=False)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Main", True)
        dpg.start_dearpygui()
        dpg.destroy_context()
        self.stop_engine()

if __name__ == "__main__":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    LunarImGui()
