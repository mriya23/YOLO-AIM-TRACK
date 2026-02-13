#ifndef SHARED_STRUCT_H
#define SHARED_STRUCT_H

// CRITICAL: pack(1) disables padding to match Python's struct.pack exactly
#pragma pack(push, 1)
struct SharedData {
    int targetX;        // Target X coordinate (pixel offset)
    int targetY;        // Target Y coordinate (pixel offset)
    bool targetFound;   // Is a target currently detected?
    float smoothing;    // Smoothing factor (from GUI)
    float humanization; // Humanization/Jitter strength
    bool rcsActive;     // Is Recoil Control System active?
    float rcsX;         // RCS Strength X
    float rcsY;         // RCS Strength Y
    float speedX;       // Aim Speed X (Horizontal multiplier)
    float speedY;       // Aim Speed Y (Vertical multiplier)
    int fov;            // Field of View radius
    bool rawInput;      // If true, targetX/Y are interpreted as Raw Deltas (Bypass smoothing)
    bool shutdown;      // Signal to close the executor
};
#pragma pack(pop)

#endif // SHARED_STRUCT_H
