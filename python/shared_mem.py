import mmap
import struct
import os

class SharedMemoryManager:
    def __init__(self, filename="aimbot_shared_mem", size=1024):
        self.filename = filename
        self.size = size
        # Strict 40-byte pack matching C++ #pragma pack(1)
        # ii?ff?ffffi?? = 4+4+1+4+4+1+4+4+4+4+4+1+1 = 40
        self.struct_format = "=ii?ff?ffffi??" 
        self.log_tick = 0
        
        if os.name == 'nt':
            self.shm = mmap.mmap(-1, self.size, tagname=filename)
        else:
            self.shm = mmap.mmap(-1, self.size)

    def write_data(self, x, y, found, smoothing, humanization, rcs, rcs_x, rcs_y, speed_x, speed_y, fov, raw_input=False, shutdown=False):
        # NaN/Inf Protection
        def safe_float(v, default=0.0):
            if v != v or v == float('inf') or v == float('-inf'): return default
            return float(v)

        smoothing = safe_float(smoothing, 3.0)
        humanization = safe_float(humanization, 0.0)
        rcs_x = safe_float(rcs_x, 0.0)
        rcs_y = safe_float(rcs_y, 0.0)
        speed_x = safe_float(speed_x, 250.0)
        speed_y = safe_float(speed_y, 10.0)
        
        # Log every 144 ticks (~1 second) to avoid IO crash
        self.log_tick += 1
        if self.log_tick >= 144:
            self.log_tick = 0
            try:
                 with open("shm_log.txt", "w") as f:
                     f.write(f"LAST_HEARTBEAT: x={x} y={y} f={found} sm={smoothing} spd={speed_x}\n")
            except: pass

        data = struct.pack(self.struct_format, x, y, found, smoothing, humanization, rcs, rcs_x, rcs_y, speed_x, speed_y, fov, raw_input, shutdown)
        self.shm.seek(0)
        self.shm.write(data)

    def close(self):
        self.shm.close()
        if os.name == 'nt' and self.fd:
            os.close(self.fd)

if __name__ == "__main__":
    # Test script
    shm = SharedMemoryManager()
    print("Writing test data to Shared Memory...")
    shm.write_data(100, 200, True, 0.5, True, False, 0.0, 0.0, 280.0, 1.0, 100)
    print("Done. Ready for C++ to read.")
