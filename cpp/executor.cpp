#include <windows.h>
#include <iostream>
#include <vector>
#include <chrono>
#include <thread>
#include <math.h>
#include <random>
#include <algorithm>
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

#ifndef SHM_NAME
    #define SHM_NAME "aimbot_shared_mem" // Default fallback
    #endif
    const char* shm_name = SHM_NAME;
    HANDLE hMapFile = NULL;

    // === RETRY LOOP: Wait for Python to create SHM ===
    std::cout << "[+] Waiting for Python Orchestrator..." << std::endl;
    for (int i = 0; i < 120; i++) { // 120 retries = 60 seconds max
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
    int tick_counter = 0;
    
    // Distribution state
    float step_x = 0.0f;
    float step_y = 0.0f;
    int steps_remaining = 0;
    
    // === PRECISION LOOP ===
    std::cout << "[+] Entering Main Loop (Heartbeat every 500ms)" << std::endl;
    auto last_heartbeat = std::chrono::high_resolution_clock::now();
    auto frame_start = std::chrono::high_resolution_clock::now();
    
    while (true) {
        frame_start = std::chrono::high_resolution_clock::now();
        
        // Safety check: pBuf pointer
        if (!pBuf) {
            std::cerr << "[X] Critical: Shared Memory Pointer LOST!" << std::endl;
            break;
        }

        if (pBuf->shutdown) {
            std::cout << "[!] Shutdown signal received." << std::endl;
            break;
        }

        /* Heartbeat removed for clean release
        auto now = std::chrono::high_resolution_clock::now();
        if (std::chrono::duration_cast<std::chrono::milliseconds>(now - last_heartbeat).count() > 500) {
            std::cout << "H" << std::flush; 
            last_heartbeat = now;
        }
        */

        if (pBuf->targetFound) {
             if (!pBuf->rawInput) {
                int raw_tx = pBuf->targetX;
                int raw_ty = pBuf->targetY;
                
                if (raw_tx != 0 || raw_ty != 0) {
                    // Reset on read (Consume)
                    pBuf->targetX = 0;
                    pBuf->targetY = 0;
                    
                    if (abs(raw_tx) < 1 && abs(raw_ty) < 1) {
                        steps_remaining = 0;
                    } else {
                        // === SAFE SMOOTHING MATH (ANTI-OVERSHOOT) ===
                        // User Input
                        float ui_smooth = std::max(1.0f, pBuf->smoothing);
                        float ui_spd_x = std::max(1.0f, pBuf->speedX); // Slider 1-500
                        float ui_spd_y = std::max(1.0f, pBuf->speedY); // Slider 1-100?
                        
                        // 1. Calculate Effective Smooth (Speed reduces smoothing)
                        // Sensitivity factor: speed 100 = base. speed 500 = 5x faster.
                        float sens_x = ui_spd_x / 100.0f;
                        float sens_y = ui_spd_y / 10.0f; // Y-Speed is usually 1-20
                        
                        // Effective smooth cannot be less than 1.0 (1.0 = Instant Lock-On)
                        // This GUARANTEES no overshoot.
                        float eff_smooth_x = std::max(1.0f, ui_smooth / sens_x);
                        float eff_smooth_y = std::max(1.0f, ui_smooth / sens_y);
                        
                        // 2. Final Move Distance
                        float total_move_x = (float)raw_tx / eff_smooth_x;
                        float total_move_y = (float)raw_ty / eff_smooth_y;

                        // 3. Humanization (Only if far enough)
                        if (pBuf->humanization > 0.01f && (abs(raw_tx) > 5 || abs(raw_ty) > 5)) {
                            total_move_x += dist(rng) * pBuf->humanization * 0.1f;
                            total_move_y += dist(rng) * pBuf->humanization * 0.1f;
                        }

                        // 4. Distribution over 5 ticks (1ms each)
                        int ticks = 5;
                        step_x = total_move_x / (float)ticks;
                        step_y = total_move_y / (float)ticks;
                        steps_remaining = ticks;
                    }
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
                // Raw Input Mode
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

        // Precise 1ms Sleep
        while (std::chrono::duration<float, std::milli>(std::chrono::high_resolution_clock::now() - frame_start).count() < 1.0f) {
             std::this_thread::yield(); 
        }
    }
    
    timeEndPeriod(1);
    UnmapViewOfFile(pBuf);
    CloseHandle(hMapFile);
    std::cout << "\n[+] Executor exiting cleanly." << std::endl;
    return 0;
}
