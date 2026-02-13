import os
import random
import string
import subprocess
import json
import shutil

# CONFIGURATION
CPP_SOURCE = os.path.join("cpp", "executor.cpp")
BUILD_DIR = "build_cache"
BUILD_CONFIG_FILE = os.path.join("lib", "config", "build_config.json")

# Trusted System Process Names (To masquerade as)
SAFE_NAMES = [
    "audiodg_helper",
    "spoolsv_worker",
    "svchost_net",
    "taskhost_ui",
    "conhost_service",
    "lsass_dump", 
    "dwm_core",
    "explorer_shell",
    "runtime_broker_v2"
]

def generate_random_string(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_junk_code():
    """Generates random C++ functions that do nothing but change the file signature."""
    junk = ""
    num_funcs = random.randint(5, 15)
    
    for i in range(num_funcs):
        func_name = f"junk_{generate_random_string(8)}"
        val = random.randint(1, 1000)
        junk += f"// Junk Code {i}\n"
        junk += f"int {func_name}(int x) {{ return x * {val} + {i}; }}\n"
    
    return junk

def build():
    print("[*] Starting Polymorphic Build Engine...")
    
    # 1. Generate Random Identity
    shm_id = f"mem_{generate_random_string(16)}"
    output_name = random.choice(SAFE_NAMES) + ".exe"
    
    print(f"    [-] Generated SHM ID: {shm_id}")
    print(f"    [-] Target Output: {output_name}")
    
    # 2. Prepare Junk Code
    junk_code = generate_junk_code()
    
    # 3. Read Source and Inject Junk
    # We cheat a bit by appending junk code to the end, or we could insert it.
    # Appending is safer for validity.
    if not os.path.exists(CPP_SOURCE):
        print(f"[!] Error: {CPP_SOURCE} not found!")
        return
        
    with open(CPP_SOURCE, "r") as f:
        source_content = f.read()
        
    # Inject Junk before main() to ensure it's compiled but not necessarily called
    # Actually, if it's not called, smart compilers might strip it.
    # To force it, we might need to verify optimization levels.
    # For now, appending verified works for changing file HASH.
    
    # DEBUG: Just copy source for now to verify base file validity
    temp_source = source_content
    # Inject Junk at the END for safety, ensuring newlines
    temp_source += "\n\n// POLYMORPHIC JUNK DATA\n" + junk_code + "\n"
    
    temp_source_path = os.path.join("cpp", "executor_temp.cpp")
    
    with open(temp_source_path, "w") as f:
        f.write(temp_source)
        
    # 4. Compile with Value Definition
    # Check for local compiler first
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_bin = os.path.join(script_dir, "compiler", "w64devkit", "bin")
    local_gpp = os.path.join(local_bin, "g++.exe")
    
    compiler_cmd = "g++"
    if os.path.exists(local_gpp):
        compiler_cmd = local_gpp
        # CRITICAL: Add bin to PATH so g++ can find 'as.exe' and 'ld.exe'
        os.environ["PATH"] = local_bin + os.pathsep + os.environ["PATH"]
    
    cmd = [
        compiler_cmd, temp_source_path, 
        "-o", output_name,
        f'-DSHM_NAME="{shm_id}"',
        "-O2", "-static",
        "-luser32", "-lkernel32", "-lwinmm" # Link libraries
    ]
    
    print(f"    [-] Compiling: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        print("[+] Compilation Successful!")
    except subprocess.CalledProcessError:
        print("[!] Compilation Failed! Do you have MinGW/G++ installed?")
        # Cleanup
        if os.path.exists(temp_source_path):
            os.remove(temp_source_path)
        return

    # 5. Cleanup Temp Source
    if os.path.exists(temp_source_path):
        os.remove(temp_source_path)

    # 6. Save Config for Python
    # Python needs to know what the Random SHM ID/Exe Name is
    build_data = {
        "shm_name": shm_id,
        "executor_name": output_name,
        "build_time": generate_random_string(5) # Just extra noise
    }
    
    os.makedirs(os.path.dirname(BUILD_CONFIG_FILE), exist_ok=True)
    with open(BUILD_CONFIG_FILE, "w") as f:
        json.dump(build_data, f, indent=4)
        
    print(f"[+] Build Config Saved: {BUILD_CONFIG_FILE}")
    
    # 7. Copy Interception DLL if exists
    dll_src = os.path.join("cpp", "interception.dll")
    dll_dst = "interception.dll"
    if os.path.exists(dll_src):
        try:
            shutil.copy(dll_src, dll_dst)
            print("[+] Interception DLL Copied to Root")
        except: pass

    print(f"[+] POLYMORPHIC BUILD COMPLETE: {output_name}")
    print("[*] You can now run 'gui.py' (it will auto-detect this build).")

if __name__ == "__main__":
    build()
