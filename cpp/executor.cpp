#include <windows.h>
#include <iostream>
#include <vector>
#include <chrono>
#include <thread>
#include <math.h>
#include <random>
#include "shared_struct.h"
#include "interception_loader.h"

// Context for Interception
InterceptionContext ctx = 0;
bool use_interception = false;

// Random number generator for humanization
std::mt19937 rng(std::random_device{}());
std::uniform_real_distribution<float> dist(-1.0f, 1.0f);

void move_mouse(int dx, int dy) {
    if (dx == 0 && dy == 0) return;
    
    if (use_interception && ctx) {
        // Send to mouse devices 11-20 (Interception standard range)
        InterceptionMouseStroke stroke = {0};
        stroke.flags = 0;
        stroke.x = dx;
        stroke.y = dy;
        stroke.information = 0;
        
        for (int i = 11; i <= 20; ++i) {
            interception_send(ctx, i, (InterceptionStroke*)&stroke, 1);
        }
    } else {
        INPUT input = { 0 };
        input.type = INPUT_MOUSE;
        input.mi.dx = dx;
        input.mi.dy = dy;
        input.mi.dwFlags = MOUSEEVENTF_MOVE;
        SendInput(1, &input, sizeof(INPUT));
    }
}

int main() {
    // === TRY LOADING INTERCEPTION ===
    const char* dll_name = "interception.dll";
    if (LoadInterception()) {
        ctx = interception_create_context();
        if (ctx) {
            use_interception = true;
            std::cout << "[+] Interception Driver: LOADED (Kernel Injection Active)" << std::endl;
        } else {
            std::cerr << "[!] Interception Loaded but Context Failed. Fallback to SendInput." << std::endl;
        }
    } else {
         std::cout << "[-] interception.dll not found. Using Standard Mouse Input." << std::endl;
    }

    const char* shm_name = "aimbot_shared_mem";
    HANDLE hMapFile = NULL;

    // === RETRY LOOP: Wait for Python to create SHM ===
    std::cout << "[+] Waiting for Python Orchestrator..." << std::endl;
    for (int i = 0; i < 30; i++) { // 30 retries = 15 seconds max
        hMapFile = OpenFileMappingA(FILE_MAP_ALL_ACCESS, FALSE, shm_name);
        if (hMapFile != NULL) break;
        std::cout << "." << std::flush;
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }

    if (hMapFile == NULL) {
        std::cerr << "\n[X] TIMEOUT: Python not detected after 15s." << std::endl;
        std::cerr << "    Start gui.py first, then try again." << std::endl;
        std::cin.get(); // Pause so user can read
        return 1;
    }

    SharedData* pBuf = (SharedData*)MapViewOfFile(hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(SharedData));

    if (pBuf == NULL) {
        std::cerr << "[X] MapViewOfFile failed." << std::endl;
        CloseHandle(hMapFile);
        std::cin.get();
        return 1;
    }

    // === PRIORITY BOOST ===
    // Critical: Executor must run at HIGH priority to maintain 1000Hz loop
    // when the game is hogging CPU resources. Otherwise, input lag occurs.
    if (!SetPriorityClass(GetCurrentProcess(), HIGH_PRIORITY_CLASS)) {
        std::cerr << "[!] Failed to set HIGH_PRIORITY_CLASS" << std::endl;
    } else {
        std::cout << "[+] Process Priority: HIGH" << std::endl;
    }

    std::cout << "\n[+] C++ Muscle CONNECTED! (1000Hz Loop)" << std::endl;
    std::cout << "[+] Smoothing & Movement handled by C++." << std::endl;

    timeBeginPeriod(1);

    float acc_x = 0.0f;
    float acc_y = 0.0f;
    int debug_counter = 0;
    
    // Consume + Distribute pattern:
    // Python writes target delta at ~144Hz. C++ runs at ~1000Hz.
    // OLD BUG: C++ read the SAME stale delta 7x → 7x overshoot.
    // FIX: Consume (zero) target on read, distribute movement over N ticks.
    float remaining_dx = 0.0f;
    float remaining_dy = 0.0f;
    float step_x = 0.0f;
    float step_y = 0.0f;
    int steps_remaining = 0;
    // ADAPTIVE DISTRIBUTION STATE
    auto last_update_time = std::chrono::high_resolution_clock::now();
    int current_distribute_ticks = 7; // Default start

    // === DISABLE POWER THROTTLING (EcoQoS) ===
    // Prevents Windows 11 from throttling this process when in background
    PROCESS_POWER_THROTTLING_STATE PowerThrottling;
    RtlZeroMemory(&PowerThrottling, sizeof(PowerThrottling));
    PowerThrottling.Version = PROCESS_POWER_THROTTLING_CURRENT_VERSION;
    PowerThrottling.ControlMask = PROCESS_POWER_THROTTLING_EXECUTION_SPEED;
    PowerThrottling.StateMask = 0; // 0 = Disable Throttling
    
    SetProcessInformation(GetCurrentProcess(), ProcessPowerThrottling, &PowerThrottling, sizeof(PowerThrottling));
    std::cout << "[+] Power Throttling: DISABLED" << std::endl;

    // === PRECISION LOOP (Hybrid Spinlock) ===
    auto frame_start = std::chrono::high_resolution_clock::now();
    
    while (true) {
        frame_start = std::chrono::high_resolution_clock::now();
        
        if (pBuf->shutdown) break;

        // ... work ...
        // Debug output
        debug_counter++;
        if (debug_counter >= 1000) {
            debug_counter = 0;
            std::cout << "[DBG] FPS_Ticks=" << current_distribute_ticks 
                      << " sm=" << pBuf->smoothing 
                      << " rem=(" << steps_remaining << ")" << std::endl;
        }

        if (pBuf->targetFound) {
             // ... COPY EXISTING LOGIC ...
             if (!pBuf->rawInput) {
                int raw_tx = pBuf->targetX;
                int raw_ty = pBuf->targetY;
                
                if (raw_tx != 0 || raw_ty != 0) {
                     // Fixed 5ms strategy
                    int current_distribute_ticks = 5; 
                    pBuf->targetX = 0;
                    pBuf->targetY = 0;
                    
                    if (abs(raw_tx) < 2 && abs(raw_ty) < 2) {
                        steps_remaining = 0;
                        goto frame_end; // Skip to wait
                    }

                    // Calculate smooth pull for this batch
                    // UNCLAMPED: Allow 0.01 (Rage Mode)
                    float smooth = max(0.01f, pBuf->smoothing);
                    float sensitivity = 1.5f; 
                    
                    float total_move_x = (float)raw_tx * (sensitivity / smooth);
                    float total_move_y = (float)raw_ty * (sensitivity / smooth);
                    
                    if (pBuf->humanization > 0.01f && (abs(raw_tx) > 5 || abs(raw_ty) > 5)) {
                        total_move_x += dist(rng) * pBuf->humanization * 0.1f;
                        total_move_y += dist(rng) * pBuf->humanization * 0.1f;
                    }
                    
                    step_x = total_move_x / current_distribute_ticks;
                    step_y = total_move_y / current_distribute_ticks;
                    steps_remaining = current_distribute_ticks;
                }
                
                if (steps_remaining > 0) {
                    float move_x = step_x;
                    float move_y = step_y;
                    
                    if (pBuf->rcsActive) {
                        move_y += (pBuf->rcsY * 0.01f);
                        move_x += (pBuf->rcsX * 0.01f);
                    }
                    
                    acc_x += move_x;
                    acc_y += move_y;
                    steps_remaining--;
                }

                int ix = (int)acc_x;
                int iy = (int)acc_y;
                acc_x -= ix;
                acc_y -= iy;

                if (ix != 0 || iy != 0) {
                    move_mouse(ix, iy);
                }
            } else {
                // Raw
                int dx = pBuf->targetX;
                int dy = pBuf->targetY;
                if (dx != 0 || dy != 0) {
                    move_mouse(dx, dy);
                    pBuf->targetX = 0;
                    pBuf->targetY = 0;
                }
            }
        } else {
            acc_x = 0.0f;
            acc_y = 0.0f;
            steps_remaining = 0;
        }

        frame_end:
        // BUSY WAIT for consistent 1000Hz
        while (std::chrono::duration<float, std::milli>(std::chrono::high_resolution_clock::now() - frame_start).count() < 1.0f) {
            // Spin to burn time (Precise < 1ms)
            // _mm_pause(); // Intrinsic not included, just empty loop or yield
             std::this_thread::yield(); 
        }
    }

    timeEndPeriod(1);
    UnmapViewOfFile(pBuf);
    CloseHandle(hMapFile);
    return 0;
}
