#ifndef INTERCEPTION_LOADER_H
#define INTERCEPTION_LOADER_H

#include <windows.h>
#include <iostream>

typedef void *InterceptionContext;
typedef int InterceptionDevice;
typedef int InterceptionPrecedence;
typedef unsigned short InterceptionFilter;
typedef int (*InterceptionPredicate)(InterceptionDevice device);

#define INTERCEPTION_MAX_KEYBOARD 10
#define INTERCEPTION_MAX_MOUSE 10
#define INTERCEPTION_MAX_DEVICE ((INTERCEPTION_MAX_KEYBOARD) + (INTERCEPTION_MAX_MOUSE))

#define INTERCEPTION_KEYBOARD(index) ((index) + 1)
#define INTERCEPTION_MOUSE(index) ((INTERCEPTION_MAX_KEYBOARD) + (index) + 1)

#define INTERCEPTION_FILTER_MOUSE_NONE 0x0000
#define INTERCEPTION_FILTER_MOUSE_ALL 0xFFFF
#define INTERCEPTION_FILTER_MOUSE_MOVE 0x1000

typedef struct {
    unsigned short state;
    unsigned short flags;
    short rolling;
    int x;
    int y;
    unsigned int information;
} InterceptionMouseStroke;

typedef struct {
    unsigned short code;
    unsigned short state;
    unsigned int information;
} InterceptionKeyStroke;

typedef char InterceptionStroke[18];

// Function Pointers
typedef InterceptionContext (*pfn_interception_create_context)(void);
typedef void (*pfn_interception_destroy_context)(InterceptionContext context);
typedef InterceptionPrecedence (*pfn_interception_get_precedence)(InterceptionContext context, InterceptionDevice device);
typedef void (*pfn_interception_set_filter)(InterceptionContext context, InterceptionPredicate predicate, InterceptionFilter filter);
typedef int (*pfn_interception_wait)(InterceptionContext context);
typedef int (*pfn_interception_receive)(InterceptionContext context, InterceptionDevice device, InterceptionStroke *stroke, unsigned int nstroke);
typedef int (*pfn_interception_send)(InterceptionContext context, InterceptionDevice device, const InterceptionStroke *stroke, unsigned int nstroke);

// Global Pointers
pfn_interception_create_context interception_create_context = NULL;
pfn_interception_destroy_context interception_destroy_context = NULL;
pfn_interception_send interception_send = NULL;

HMODULE hInterceptionDLL = NULL;

bool LoadInterception() {
    hInterceptionDLL = LoadLibraryA("interception.dll");
    if (!hInterceptionDLL) return false;

    interception_create_context = (pfn_interception_create_context)GetProcAddress(hInterceptionDLL, "interception_create_context");
    interception_destroy_context = (pfn_interception_destroy_context)GetProcAddress(hInterceptionDLL, "interception_destroy_context");
    interception_send = (pfn_interception_send)GetProcAddress(hInterceptionDLL, "interception_send");

    return (interception_create_context && interception_send);
}

// Simple Mouse Move Wrapper
void InterceptionMove(InterceptionContext ctx, int dx, int dy) {
    if (!ctx || !interception_send) return;
    
    InterceptionMouseStroke stroke = {0};
    stroke.flags = 0; // Relative move (0). Absolute is 0x001.
    stroke.x = dx;
    stroke.y = dy;
    
    // Send to all mouse devices (1-10) or specific one? 
    // Usually sending to first valid mouse device works, or loop 11-20.
    // Better to send to INTERCEPTION_MOUSE(0) if we assume one main mouse.
    // Or iterate until success? 
    // Most robust: Send to Device 11 (First Mouse)
    
    interception_send(ctx, INTERCEPTION_MOUSE(0), (InterceptionStroke*)&stroke, 1);
}

#endif
