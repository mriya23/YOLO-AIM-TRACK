#pragma once
/*
 * Lunar Aimbot C++ Engine
 * Handles: Target Selection, Kalman Tracking, PD Aim Controller, Mouse Output
 * Python pushes YOLO detections via AimbotPushDetections()
 * C++ runs independent 144Hz aim loop
 */

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <mmsystem.h>
#pragma comment(lib, "winmm.lib")
#include <cmath>
#include <mutex>
#include <shared_mutex>
#include <thread>
#include <atomic>
#include <vector>
#include <string>
#include <fstream>
#include <chrono>
#include <algorithm>
#include <cstring>

#include "nlohmann/json.hpp"
using json = nlohmann::json;

// ============================================================================
// CONFIG: Hot-reloadable JSON config
// ============================================================================
struct AimbotConfig {
    mutable std::shared_mutex mtx;
    std::string path;
    double last_mtime = 0;

    // Aim
    bool enabled = true;
    double smoothing = 1.99;
    double x_speed = 429.0;
    double y_speed = 0.1;
    int fov_radius = 87;
    double conf_thres = 0.30;
    double aim_point_ratio = 0.12;
    int roi_size = 320;

    // Triggerbot
    bool triggerbot_enabled = false;
    double trigger_delay = 0.18;
    int trigger_radius = 14;

    // RCS
    bool rcs_enabled = false;
    int rcs_strength_x = 7;
    int rcs_strength_y = 6;

    // Headless
    bool headless = false;

    void load(const std::string& config_path) {
        std::unique_lock lock(mtx);
        path = config_path;
        try {
            std::ifstream f(path);
            if (!f.is_open()) return;
            json j = json::parse(f);

            enabled = j.value("enabled", true);
            smoothing = j.value("smoothing", 1.99);
            x_speed = j.value("x_speed", 429.0);
            y_speed = j.value("y_speed", 0.1);
            fov_radius = j.value("fov_radius", 87);
            conf_thres = j.value("conf_thres", 0.30);
            aim_point_ratio = j.value("aim_point_ratio", 0.12);
            roi_size = j.value("roi_size", 320);
            triggerbot_enabled = j.value("triggerbot_enabled", false);
            trigger_delay = j.value("trigger_delay", 0.18);
            trigger_radius = j.value("trigger_radius", 14);
            rcs_enabled = j.value("rcs_enabled", false);
            rcs_strength_x = j.value("rcs_strength_x", 7);
            rcs_strength_y = j.value("rcs_strength_y", 6);
            headless = j.value("headless", false);

            // Update mtime
            WIN32_FILE_ATTRIBUTE_DATA fad;
            if (GetFileAttributesExA(path.c_str(), GetFileExInfoStandard, &fad)) {
                ULARGE_INTEGER uli;
                uli.LowPart = fad.ftLastWriteTime.dwLowDateTime;
                uli.HighPart = fad.ftLastWriteTime.dwHighDateTime;
                last_mtime = static_cast<double>(uli.QuadPart);
            }
        }
        catch (...) {}
    }

    void reload_if_changed() {
        if (path.empty()) return;
        WIN32_FILE_ATTRIBUTE_DATA fad;
        if (!GetFileAttributesExA(path.c_str(), GetFileExInfoStandard, &fad)) return;
        ULARGE_INTEGER uli;
        uli.LowPart = fad.ftLastWriteTime.dwLowDateTime;
        uli.HighPart = fad.ftLastWriteTime.dwHighDateTime;
        double mtime = static_cast<double>(uli.QuadPart);
        {
            std::shared_lock lock(mtx);
            if (mtime <= last_mtime) return;
        }
        load(path);
    }

    // Thread-safe getters
    template<typename T>
    T get(T AimbotConfig::*member) const {
        std::shared_lock lock(mtx);
        return this->*member;
    }

    // Snapshot for aim loop (avoid repeated locking)
    struct Snapshot {
        bool enabled;
        double smoothing, x_speed, y_speed;
        int fov_radius;
        double aim_point_ratio;
        int roi_size;
        bool triggerbot_enabled;
        double trigger_delay;
        int trigger_radius;
        bool rcs_enabled;
        int rcs_strength_x, rcs_strength_y;
    };

    Snapshot snapshot() const {
        std::shared_lock lock(mtx);
        return {enabled, smoothing, x_speed, y_speed, fov_radius,
                aim_point_ratio, roi_size, triggerbot_enabled,
                trigger_delay, trigger_radius, rcs_enabled,
                rcs_strength_x, rcs_strength_y};
    }
};

// ============================================================================
// TARGET STATE: Simplified Kalman Filter (direct port from Python)
// ============================================================================
struct TargetState {
    mutable std::mutex mtx;
    bool active = false;

    // Kalman state: [x, y, vx, vy]
    double state[4] = {0, 0, 0, 0};
    // Covariance (simplified, only key elements)
    double P[4][4] = {};
    // Process noise
    double Q[4] = {0.1, 0.1, 0.1, 0.1};
    // Measurement noise
    double R[2] = {5.0, 5.0};

    double last_update_time = 0.0;
    double conf = 0.0;
    int box[4] = {0, 0, 0, 0}; // x, y, w, h
    int target_id = 0;

    TargetState() {
        // Init covariance as identity
        for (int i = 0; i < 4; i++) P[i][i] = 1.0;
    }

    void update(double x, double y, double c, const int b[4], double time_now) {
        std::lock_guard<std::mutex> lock(mtx);
        double dt = (last_update_time > 0) ? (time_now - last_update_time) : 0.005;
        dt = std::max(std::min(dt, 0.050), 0.001);

        // Target switch check
        if (active) {
            double jump = std::hypot(x - state[0], y - state[1]);
            if (jump > 120.0) {
                target_id++;
                state[0] = x; state[1] = y;
                state[2] = 0; state[3] = 0;
                for (int i = 0; i < 4; i++)
                    for (int j = 0; j < 4; j++)
                        P[i][j] = (i == j) ? 5.0 : 0.0;
            }
        } else {
            state[0] = x; state[1] = y;
            state[2] = 0; state[3] = 0;
            active = true;
        }

        // Predict: x += vx*dt, y += vy*dt
        state[0] += state[2] * dt;
        state[1] += state[3] * dt;

        // Covariance predict (simplified)
        P[0][0] += P[2][2] * dt * dt + Q[0];
        P[1][1] += P[3][3] * dt * dt + Q[1];
        P[2][2] += Q[2];
        P[3][3] += Q[3];

        // Update
        double ex = x - state[0];
        double ey = y - state[1];

        double s11 = P[0][0] + R[0];
        double s22 = P[1][1] + R[1];

        double k11 = P[0][0] / s11;
        double k22 = P[1][1] / s22;
        double k31 = (P[2][2] * dt) / s11;
        double k42 = (P[3][3] * dt) / s22;

        state[0] += k11 * ex;
        state[1] += k22 * ey;
        state[2] += k31 * ex;
        state[3] += k42 * ey;

        P[0][0] *= (1.0 - k11);
        P[1][1] *= (1.0 - k22);

        conf = c;
        std::memcpy(this->box, b, sizeof(int) * 4);
        last_update_time = time_now;
    }

    struct Snapshot {
        double x, y, vx, vy;
        double last_update;
        int target_id;
        bool valid;
    };

    Snapshot get_snapshot() const {
        std::lock_guard<std::mutex> lock(mtx);
        if (!active) return {0, 0, 0, 0, 0, 0, false};
        return {state[0], state[1], state[2], state[3],
                last_update_time, target_id, true};
    }

    void apply_motion(double dx, double dy) {
        std::lock_guard<std::mutex> lock(mtx);
        if (active) {
            state[0] -= dx;
            state[1] -= dy;
        }
    }

    // For display thread
    struct DisplayData {
        double x, y;
        bool active;
        int box[4];
    };

    DisplayData current_data() const {
        std::lock_guard<std::mutex> lock(mtx);
        DisplayData d;
        d.x = state[0]; d.y = state[1]; d.active = active;
        std::memcpy(d.box, box, sizeof(int) * 4);
        return d;
    }

    void clear() {
        std::lock_guard<std::mutex> lock(mtx);
        active = false;
    }
};

// ============================================================================
// DETECTION: Data passed from Python
// ============================================================================
struct Detection {
    double x1, y1, x2, y2, conf;
};

// ============================================================================
// MOUSE COMMAND BUFFER: C++ computes deltas, Python sends via Interception
// ============================================================================
struct MouseCommandBuffer {
    std::atomic<int> pending_dx{0};
    std::atomic<int> pending_dy{0};
    std::atomic<bool> pending_click{false};

    void queue_move(int dx, int dy) {
        pending_dx.fetch_add(dx, std::memory_order_relaxed);
        pending_dy.fetch_add(dy, std::memory_order_relaxed);
    }

    void queue_click() {
        pending_click.store(true, std::memory_order_release);
    }

    // Called by Python to drain accumulated deltas
    void pop(int* out_dx, int* out_dy, int* out_click) {
        *out_dx = pending_dx.exchange(0, std::memory_order_relaxed);
        *out_dy = pending_dy.exchange(0, std::memory_order_relaxed);
        *out_click = pending_click.exchange(false, std::memory_order_relaxed) ? 1 : 0;
    }
};

// ============================================================================
// AIMBOT CORE: The main engine
// ============================================================================
class AimbotEngine {
public:
    AimbotConfig config;
    TargetState target_state;
    MouseCommandBuffer mouse_cmds;

    std::atomic<bool> running{false};
    std::atomic<bool> aimbot_enabled{true};
    std::atomic<int> current_fps{0};

    int screen_center_x = 0;
    int screen_center_y = 0;

    // Detection buffer (lock-free double buffer)
    struct DetectionFrame {
        std::vector<Detection> dets;
        int roi_left = 0, roi_top = 0;
        int roi_size = 320;
        double timestamp = 0;
    };
    std::mutex det_mtx;
    DetectionFrame det_buffer;
    std::atomic<bool> new_dets_available{false};
    std::atomic<int> last_target_valid{0};  // debug: 1 if find_target last returned valid

    // Aim thread
    std::thread aim_thread;

    // Internal aim state
    int current_target_id = 0;
    double prev_error_x = 0, prev_error_y = 0;
    double v_current_x = 0, v_current_y = 0;
    double last_shot_time = 0;

    // Sub-pixel accumulators
    double acc_x = 0.0;
    double acc_y = 0.0;

    AimbotEngine() = default;
    ~AimbotEngine() { stop(); }

    void init(const char* config_path) {
        config.load(config_path);

        screen_center_x = GetSystemMetrics(SM_CXSCREEN) / 2;
        screen_center_y = GetSystemMetrics(SM_CYSCREEN) / 2;

        // High-precision timer
        timeBeginPeriod(1);

        // DPI awareness
        typedef HRESULT(WINAPI* SetDpiFunc)(int);
        HMODULE shcore = LoadLibraryA("shcore.dll");
        if (shcore) {
            auto fn = (SetDpiFunc)GetProcAddress(shcore, "SetProcessDpiAwareness");
            if (fn) fn(1);
        }
    }

    // Called from Python after each YOLO inference
    void push_detections(const Detection* dets, int count,
                         int roi_left, int roi_top, int roi_size) {
        std::lock_guard<std::mutex> lock(det_mtx);
        det_buffer.dets.assign(dets, dets + count);
        det_buffer.roi_left = roi_left;
        det_buffer.roi_top = roi_top;
        det_buffer.roi_size = roi_size;
        det_buffer.timestamp = get_time();
        new_dets_available.store(true, std::memory_order_release);
    }

    void set_screen_center(int cx, int cy) {
        screen_center_x = cx;
        screen_center_y = cy;
    }

    void toggle() {
        aimbot_enabled.store(!aimbot_enabled.load());
        Beep(aimbot_enabled.load() ? 800 : 400, 100);
    }

    void start() {
        if (running.load()) return;
        running.store(true);
        if (!aimbot_enabled.load()) toggle();
        aim_thread = std::thread(&AimbotEngine::aim_loop, this);
    }

    void stop() {
        running.store(false);
        if (aim_thread.joinable()) aim_thread.join();
        timeEndPeriod(1);
    }

    int get_fps() const { return current_fps.load(); }

private:
    static double get_time() {
        static LARGE_INTEGER freq;
        static bool init = false;
        if (!init) { QueryPerformanceFrequency(&freq); init = true; }
        LARGE_INTEGER now;
        QueryPerformanceCounter(&now);
        return static_cast<double>(now.QuadPart) / static_cast<double>(freq.QuadPart);
    }

    // Execute mouse move/click in C++ (no Python round-trip = stable FPS when locked)
    static void do_move_relative(int dx, int dy);
    static void do_click(int button);

    // ========================================================================
    // TARGET SELECTION (direct port from Python find_target)
    // ========================================================================
    struct TargetInfo {
        int box[4]; // x, y, w, h
        double screen_x, screen_y;
        double conf;
        bool valid;
    };

    TargetInfo find_target(const std::vector<Detection>& dets,
                           int roi_left, int roi_top, int roi_size,
                           const AimbotConfig::Snapshot& cfg) {
        TargetInfo best = {};
        best.valid = false;
        if (dets.empty()) return best;

        double fov = static_cast<double>(cfg.fov_radius);
        double aim_ratio = cfg.aim_point_ratio;
        double center = roi_size / 2.0;
        double best_score = 1e18;

        // Get current target for persistence
        auto snap = target_state.current_data();
        double curr_tx = snap.x, curr_ty = snap.y;
        bool curr_active = snap.active;

        for (const auto& det : dets) {
            double w = det.x2 - det.x1;
            double h = det.y2 - det.y1;
            if (w <= 0 || h <= 0) continue;

            // Geometric filter: skip only very wide (e.g. walls). 2.0 = very loose so blue box = lock
            if (w > h * 2.0) continue;

            double bx = (det.x1 + det.x2) / 2.0;
            double by = (det.y1 + det.y2) / 2.0;
            double aim_y = det.y1 + (h * aim_ratio);

            double dist_to_center = std::hypot(bx - center, by - center);
            // FOV: minimal 230 = hampir seluruh ROI 320x320 (max dist dari center ~226) supaya titik hijau pasti muncul
            double effective_fov = std::max(fov, 230.0);
            if (dist_to_center > effective_fov) continue;

            // Target persistence (anti-switch)
            double persistence_bonus = 1.0;
            if (curr_active) {
                double dist_to_prev = std::hypot(
                    roi_left + bx - curr_tx,
                    roi_top + by - curr_ty);
                if (dist_to_prev < 40.0) {
                    persistence_bonus = 0.5;
                }
            }

            double score = dist_to_center * (1.2 - det.conf) * persistence_bonus;
            if (score < best_score) {
                best_score = score;
                best.box[0] = static_cast<int>(det.x1);
                best.box[1] = static_cast<int>(det.y1);
                best.box[2] = static_cast<int>(w);
                best.box[3] = static_cast<int>(h);
                best.screen_x = roi_left + bx;
                best.screen_y = roi_top + aim_y;
                best.conf = det.conf;
                best.valid = true;
            }
        }
        return best;
    }

    // ========================================================================
    // TRIGGERBOT
    // ========================================================================
    void triggerbot(double target_dist, const AimbotConfig::Snapshot& cfg) {
        if (!cfg.triggerbot_enabled) return;
        if (target_dist <= cfg.trigger_radius) {
            double now = get_time();
            if (now - last_shot_time > cfg.trigger_delay) {
                mouse_cmds.queue_click();
                last_shot_time = now;
            }
        }
    }

    // ========================================================================
    // AIM LOOP v15: Detection-Gated + Interpolated Output
    // ========================================================================
    // v14 problem: 1 move per detection = choppy at 30fps
    // v13 problem: 200Hz loop with stale data = 6× overshoot
    // v15 solution: Compute correct TOTAL move from FRESH detection,
    //              then SPREAD it across ~6 sub-frames at 200Hz.
    //              Same total displacement (no overshoot) + smooth delivery.
    // ========================================================================
    // ========================================================================
    // AIM LOOP v16: Continuous Velocity Filter (BMad Architecture)
    // ========================================================================
    // v15 problem: Budget-based. Resetting budget on new detection causes spikes.
    // v16 solution: Velocity-based. Persistent 'current_v' smoothed via LPF.
    //              New detections update 'target_v' (steering).
    //              Ensures 200Hz smooth motion and zero-overshoot convergence.
    // ========================================================================
    // ========================================================================
    // AIM LOOP v17: Smart Braking (BMad Architecture)
    // ========================================================================
    // v16 problem: LPF momentum causes "skidding" past target (Overshoot)
    // v17 solution: Smart Braking.
    //              1. Instant Stop if we overshoot (error sign flips).
    //              2. Arrival Clamp: don't move faster than distance remaining.
    //              3. Deadzone Kill: if < 1.0px, cut velocity to 0.
    //              Ensures mathematical convergence without momentum spillover.
    // ========================================================================
    void aim_loop() {
        acc_x = acc_y = 0.0;
        double current_vx = 0.0, current_vy = 0.0;
        
        // Track previous error to detect overshoot (sign flip)
        double last_ex = 0.0, last_ey = 0.0;

        double conf_check_time = 0.0;
        int frame_counter = 0;
        double fps_start = get_time();

        while (running.load()) {
            double t_now = get_time();

            // Config hot-reload every 1s
            if (t_now - conf_check_time > 1.0) {
                config.reload_if_changed();
                conf_check_time = t_now;
            }

            // FPS counter
            if (t_now - fps_start >= 1.0) {
                current_fps.store(frame_counter);
                frame_counter = 0;
                fps_start = t_now;
            }

            // Hotkey check: F1 toggle
            if (GetAsyncKeyState(VK_F1) & 1) {
                toggle();
            }
            // F2 exit
            if (GetAsyncKeyState(VK_F2) & 1) {
                running.store(false);
                break;
            }

            auto cfg = config.snapshot();

            // ============================================================
            // STEP 1: Process new detection (Updates Target Velocity)
            // ============================================================
            double target_vx = 0.0, target_vy = 0.0;
            double ex = 0.0, ey = 0.0; // Current error
            bool ads_active = (GetAsyncKeyState(VK_RBUTTON) < 0);
            bool tracking = false;

            if (new_dets_available.exchange(false)) {
                DetectionFrame frame;
                {
                    std::lock_guard<std::mutex> lock(det_mtx);
                    frame = det_buffer;
                }
                auto target = find_target(frame.dets, frame.roi_left,
                                           frame.roi_top, frame.roi_size, cfg);
                last_target_valid.store(target.valid ? 1 : 0);
                if (target.valid) {
                    target_state.update(target.screen_x, target.screen_y,
                                       target.conf, target.box, get_time());
                }
            }

            // ============================================================
            // STEP 2: Calculate Steering (Update Target Velocity)
            // ============================================================
            if (aimbot_enabled.load() && cfg.enabled && ads_active) {
                auto snap = target_state.get_snapshot();
                if (snap.valid) {
                    ex = snap.x - screen_center_x;
                    ey = snap.y - screen_center_y;
                    double dist = std::hypot(ex, ey);

                    if (dist >= 1.0) { // Deadzone 1.0px
                        tracking = true;
                        triggerbot(dist, cfg);

                        // Sensitivity (kp) 
                        double kp = (cfg.x_speed / 1000.0) / std::max(cfg.smoothing, 1.0);
                        double kp_y = (std::max(cfg.y_speed / 1000.0, cfg.x_speed / 1000.0 * 0.4))
                                      / std::max(cfg.smoothing, 1.0);

                        kp = std::max(0.01, std::min(0.8, kp));
                        kp_y = std::max(0.01, std::min(0.8, kp_y));

                        // Target Velocity
                        target_vx = (ex * kp) / 6.0; // 6 sub-frames
                        target_vy = (ey * kp_y) / 6.0;
                    }
                }
            }

            // ============================================================
            // STEP 3: Smart Braking & LPF
            // ============================================================
            if (!tracking) {
                // Not tracking or inside deadzone -> Kill velocity
                current_vx = 0.0;
                current_vy = 0.0;
                last_ex = 0.0; 
                last_ey = 0.0;
            } else {
                // Check for Overshoot (Sign Flip)
                // If ex and last_ex have different signs, we passed the target.
                bool overshoot_x = (std::signbit(ex) != std::signbit(last_ex)) && (std::abs(last_ex) > 0.1);
                bool overshoot_y = (std::signbit(ey) != std::signbit(last_ey)) && (std::abs(last_ey) > 0.1);

                if (overshoot_x) current_vx = 0.0; // Panic brake X
                else current_vx = (current_vx * 0.75) + (target_vx * 0.25); // Normal LPF

                if (overshoot_y) current_vy = 0.0; // Panic brake Y
                else current_vy = (current_vy * 0.75) + (target_vy * 0.25); // Normal LPF

                // Arrival Clamp: Don't move faster than distance remaining
                // If velocity > error, clamp to error
                if (std::abs(current_vx) > std::abs(ex)) current_vx = ex;
                if (std::abs(current_vy) > std::abs(ey)) current_vy = ey;
                
                last_ex = ex;
                last_ey = ey;
            }

            // ============================================================
            // STEP 4: Apply Velocity (200Hz Execution)
            // ============================================================
            acc_x += current_vx;
            acc_y += current_vy;

            int input_x = static_cast<int>(acc_x);
            int input_y = static_cast<int>(acc_y);

            acc_x -= input_x;
            acc_y -= input_y;

            if (input_x != 0 || input_y != 0) {
                mouse_cmds.queue_move(input_x, input_y);
            }

            frame_counter++;
            // 200Hz sub-frame sleep
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
        }
    }

    // High-precision sleep (spin-wait for sub-ms accuracy)
    static void sleep_precise(double seconds) {
        if (seconds <= 0) return;
        if (seconds > 0.002) {
            // Sleep for most of the time, then spin
            Sleep(static_cast<DWORD>((seconds - 0.001) * 1000.0));
        }
        // Spin-wait for the rest
        double target;
        {
            LARGE_INTEGER freq, now;
            QueryPerformanceFrequency(&freq);
            QueryPerformanceCounter(&now);
            target = static_cast<double>(now.QuadPart) / static_cast<double>(freq.QuadPart) + 
                     std::max(seconds - 0.001, 0.0);
            if (seconds <= 0.002) {
                target = static_cast<double>(now.QuadPart) / static_cast<double>(freq.QuadPart) + seconds;
            }
        }
        while (get_time() < target) {
            _mm_pause(); // CPU hint: we're spinning
        }
    }
};
