/*
 * Lunar Aimbot DLL Exports
 * extern "C" API for Python ctypes integration
 * Mouse output is done in C++ (SendInput) so Python doesn't run mouse loop = stable FPS when locked.
 */

#include "lunar_aimbot.h"
#include <intrin.h>  // for _mm_pause

// ============================================================================
// MOUSE OUTPUT (in C++ to avoid Python GIL/round-trip when lock-on)
// ============================================================================
void AimbotEngine::do_move_relative(int dx, int dy) {
    if (dx == 0 && dy == 0) return;
    INPUT input = { 0 };
    input.type = INPUT_MOUSE;
    input.mi.dx = dx;
    input.mi.dy = dy;
    input.mi.dwFlags = MOUSEEVENTF_MOVE;
    SendInput(1, &input, sizeof(INPUT));
}

void AimbotEngine::do_click(int button) {
    INPUT input = { 0 };
    input.type = INPUT_MOUSE;
    if (button == 0) {
        input.mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
        SendInput(1, &input, sizeof(INPUT));
        input.mi.dwFlags = MOUSEEVENTF_LEFTUP;
        SendInput(1, &input, sizeof(INPUT));
    } else {
        input.mi.dwFlags = MOUSEEVENTF_RIGHTDOWN;
        SendInput(1, &input, sizeof(INPUT));
        input.mi.dwFlags = MOUSEEVENTF_RIGHTUP;
        SendInput(1, &input, sizeof(INPUT));
    }
}

// ============================================================================
// C API EXPORTS
// ============================================================================
extern "C" {

    // Create aimbot engine, returns opaque handle
    __declspec(dllexport) void* AimbotCreate(const char* config_path) {
        auto* engine = new AimbotEngine();
        engine->init(config_path);
        return static_cast<void*>(engine);
    }

    // Destroy engine
    __declspec(dllexport) void AimbotDestroy(void* handle) {
        if (!handle) return;
        auto* engine = static_cast<AimbotEngine*>(handle);
        engine->stop();
        delete engine;
    }

    // Start the 144Hz aim loop thread
    __declspec(dllexport) void AimbotStartAimLoop(void* handle) {
        if (!handle) return;
        static_cast<AimbotEngine*>(handle)->start();
    }

    // Stop the aim loop
    __declspec(dllexport) void AimbotStopAimLoop(void* handle) {
        if (!handle) return;
        static_cast<AimbotEngine*>(handle)->stop();
    }

    // Push YOLO detections from Python
    // data layout: [x1, y1, x2, y2, conf, x1, y1, x2, y2, conf, ...]
    // count: number of detections
    __declspec(dllexport) void AimbotPushDetections(void* handle,
                                                     const double* data, int count,
                                                     int roi_left, int roi_top,
                                                     int roi_size) {
        if (!handle || !data || count <= 0) return;
        auto* engine = static_cast<AimbotEngine*>(handle);

        // Convert flat array to Detection structs
        std::vector<Detection> dets(count);
        for (int i = 0; i < count; i++) {
            dets[i].x1   = data[i * 5 + 0];
            dets[i].y1   = data[i * 5 + 1];
            dets[i].x2   = data[i * 5 + 2];
            dets[i].y2   = data[i * 5 + 3];
            dets[i].conf = data[i * 5 + 4];
        }
        engine->push_detections(dets.data(), count, roi_left, roi_top, roi_size);
    }

    // Set screen center (call once after init)
    __declspec(dllexport) void AimbotSetScreenCenter(void* handle, int cx, int cy) {
        if (!handle) return;
        static_cast<AimbotEngine*>(handle)->set_screen_center(cx, cy);
    }

    // Toggle aimbot on/off
    __declspec(dllexport) void AimbotToggle(void* handle) {
        if (!handle) return;
        static_cast<AimbotEngine*>(handle)->toggle();
    }

    // Check if enabled
    __declspec(dllexport) int AimbotIsEnabled(void* handle) {
        if (!handle) return 0;
        return static_cast<AimbotEngine*>(handle)->aimbot_enabled.load() ? 1 : 0;
    }

    // Check if running
    __declspec(dllexport) int AimbotIsRunning(void* handle) {
        if (!handle) return 0;
        return static_cast<AimbotEngine*>(handle)->running.load() ? 1 : 0;
    }

    // Get current aim loop FPS
    __declspec(dllexport) int AimbotGetFPS(void* handle) {
        if (!handle) return 0;
        return static_cast<AimbotEngine*>(handle)->get_fps();
    }

    // Reload config from disk
    __declspec(dllexport) void AimbotReloadConfig(void* handle) {
        if (!handle) return;
        static_cast<AimbotEngine*>(handle)->config.reload_if_changed();
    }

    // Get target state for display (Python draws the overlay)
    // Returns: [x, y, active(0/1), box_x, box_y, box_w, box_h]
    __declspec(dllexport) void AimbotGetTargetData(void* handle, double* out) {
        if (!handle || !out) return;
        auto* engine = static_cast<AimbotEngine*>(handle);
        auto data = engine->target_state.current_data();
        out[0] = data.x;
        out[1] = data.y;
        out[2] = data.active ? 1.0 : 0.0;
        out[3] = static_cast<double>(data.box[0]);
        out[4] = static_cast<double>(data.box[1]);
        out[5] = static_cast<double>(data.box[2]);
        out[6] = static_cast<double>(data.box[3]);
    }

    // Pop accumulated mouse commands (Python polls this + sends via Interception)
    __declspec(dllexport) void AimbotPopMouseCommands(void* handle,
                                                       int* out_dx, int* out_dy,
                                                       int* out_click) {
        if (!handle) { *out_dx = 0; *out_dy = 0; *out_click = 0; return; }
        static_cast<AimbotEngine*>(handle)->mouse_cmds.pop(out_dx, out_dy, out_click);
    }

    // Debug: 1 if find_target last returned valid, 0 otherwise
    __declspec(dllexport) int AimbotGetLastTargetValid(void* handle) {
        if (!handle) return 0;
        return static_cast<AimbotEngine*>(handle)->last_target_valid.load();
    }
}
