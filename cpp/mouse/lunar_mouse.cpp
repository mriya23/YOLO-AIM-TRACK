#include <windows.h>
#include <cmath>

extern "C" {
    __declspec(dllexport) void MoveRelative(int x, int y) {
        INPUT input = { 0 };
        input.type = INPUT_MOUSE;
        input.mi.dx = x;
        input.mi.dy = y;
        input.mi.dwFlags = MOUSEEVENTF_MOVE;
        SendInput(1, &input, sizeof(INPUT));
    }

    __declspec(dllexport) void Click(int button) {
        INPUT input = { 0 };
        input.type = INPUT_MOUSE;
        
        if (button == 0) { // Left Click
            input.mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
            SendInput(1, &input, sizeof(INPUT));
            input.mi.dwFlags = MOUSEEVENTF_LEFTUP;
            SendInput(1, &input, sizeof(INPUT));
        }
        else if (button == 1) { // Right Click
            input.mi.dwFlags = MOUSEEVENTF_RIGHTDOWN;
            SendInput(1, &input, sizeof(INPUT));
            input.mi.dwFlags = MOUSEEVENTF_RIGHTUP;
            SendInput(1, &input, sizeof(INPUT));
        }
    }
}
