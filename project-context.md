---
project_name: 'Yolo Aimbot'
user_name: 'Riski'
date: '2026-02-11'
sections_completed: ['technology_stack', 'critical_rules']
existing_patterns_found: 4
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Core Logic**: Python 3.x (Orchestrator) + C++17 (High-Performance Aim Loop via DLL)
- **AI Detection**: YOLO (Ultralytics) + DXCam (Fast Screen Capture)
- **Input Driver**: Interception Driver (via `interception` Python wrapper or C++ wrapper) - **CRITICAL: DO NOT USE `win32api.mouse_event` for aim movement**
- **GUI**: CustomTkinter (Python)
- **Build System**: CMake (for C++)

## Critical Implementation Rules

### Language-Specific Rules (Hybrid Python/C++)

- **DLL Interface**: 
    - Python loads C++ logic via `ctypes`.
    - `lunar_aimbot.dll` exports `AimbotCreate`, `AimbotPushDetections`, `AimbotStartAimLoop`, etc.
    - **Data Flow**: Python -> Detections -> C++ Queue -> C++ Aim Loop -> Mouse Output.
    - **Never** put heavy logic in the Python main loop; offload to C++ or threaded workers.

### Framework-Specific Rules (YOLO & DXCam)

- **DXCam**:
    - Use `dxcam.create(output_color="BGR")` for OpenCV compatibility.
    - Capture loop must run in a separate thread/process to avoid blocking the GUI.
- **YOLO**:
    - Inference must be optimized (TensorRT/CUDA if available).
    - Detections must be filtered by confidence threshold before sending to C++.

### Code Quality & Style Rules

- **Naming**: 
    - Python: `snake_case` for functions/variables, `PascalCase` for classes.
    - C++: `PascalCase` for exported functions, `snake_case` for internal logic.
- **Safety**:
    - All memory shared between Python and C++ must be carefully managed (use `ctypes` pointers).
    - **Thread Safety**: The C++ aim loop runs on a separate thread; ensure shared data (detections) is mutex-protected.

### Critical Don't-Miss Rules

- **ANTI-DETECTION**: 
    - **NEVER** use `pyautogui` or `mouse` or `win32api` for aiming. ONLY use the Interception driver path found in `lib/mouse_controller.py` or the C++ engine.
    - **SMOOTHING**: Aim movement must be smoothed (Low Pass Filter / PID) in C++. Do not snap instantly to target.
    - **PERFORMANCE**: The aim loop MUST run at >144Hz. Python GC pauses are fatal; keep Python allocations minimal in the hot loop.
- **BUILD**:
    - Always run `build_aimbot.bat` after modifying C++ code.
