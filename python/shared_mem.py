import mmap
import struct
import os

class SharedMemoryManager:
    def __init__(self, filename="aimbot_shared_mem", size=1024):
        self.filename = f"/tmp/{filename}" if os.name != 'nt' else filename
        self.size = size
        # '=' prefix = standard size, NO alignment padding (matches C++ #pragma pack(1))
        # WITHOUT '=': Python adds 3-byte padding after bool before float = DATA CORRUPTION
        self.struct_format = "=ii?ff?ffib?" 
        
        if os.name == 'nt':
            # Create RAM-backed named shared memory (No Disk I/O)
            self.shm = mmap.mmap(-1, self.size, tagname=filename)
            self.fd = None # No file handle needed
        else:
            # Unix-like systems (if needed)
            self.shm = mmap.mmap(-1, self.size)

    def write_data(self, x, y, found, smoothing, humanization, rcs, rcs_x, rcs_y, fov, raw_input=False, shutdown=False):
        data = struct.pack(self.struct_format, x, y, found, smoothing, humanization, rcs, rcs_x, rcs_y, fov, raw_input, shutdown)
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
    shm.write_data(100, 200, True, 0.5, True, 100)
    print("Done. Ready for C++ to read.")
