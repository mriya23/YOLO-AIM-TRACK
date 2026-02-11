# 🎯 YOLO Aimbot Hybrid (Python + C++)

**High Performance Visual Aimbot** dengan arsitektur Hybrid:
- **Otak (Python)**: Deteksi cerdas menggunakan YOLOv8 + TensorRT.
- **Otot (C++)**: Eksekusi mouse 1000Hz via Shared Memory (Low Latency).

## 🚀 Fitur Premium
1.  **Zero Latency IPC**: Komunikasi antar proses super cepat (~0ms).
2.  **Humanization**: Gerakan mouse memiliki *micro-jitter* acak agar tidak terdeteksi robotik.
3.  **Dynamic RCS**: Recoil Control System yang bisa diatur kekuatannya (X/Y) secara live.
4.  **Hot-Reload Config**: Ganti settingan di `config.json` saat aimbot jalan, langsung berubah!

## 📦 Cara Install & Jalanin
1.  Pastikan **Python 3.10+** dan **Visual Studio 2022** (untuk compiler C++) terinstall.
2.  Install dependencies Python:
    ```bash
    pip install -r requirements.txt
    ```
    *(Pastikan library standar seperti `dxcam`, `ultralytics`, `opencv-python`, `pywin32` terinstall)*
3.  **Compile C++ Executor** (Cukup sekali):
    Jalankan `build_cpp.bat`. Pastikan muncul "Build Successful".
4.  **Mulai Aimbot**:
    Klik dua kali **`run_hybrid.bat`**.

## ⚙️ Konfigurasi (`lib/config/config.json`)
File ini bisa diedit saat aimbot berjalan. Cukup save, dan aimbot akan otomatis update.

```json
{
    "roi_size": 320,       // Ukuran kotak deteksi (tengah layar)
    "conf_thres": 0.45,    // Sensitivitas deteksi (0.1 - 1.0)
    "smoothing": 0.2,      // Kehalusan aim (makin kecil makin pelan/halus)
    "humanization": 1.5,   // Kekuatan jitter acak (pixel)
    "rcs_enabled": true,   // Nyalain Recoil Control?
    "rcs_strength_x": 0.5, // Tahan recoil ke samping (Horizontal)
    "rcs_strength_y": 2.0, // Tahan recoil ke atas (Vertikal)
    "fov_radius": 100      // Radius lingkaran FOV
}
```

## 🛠️ Struktur Folder
- `python/`: Source code Python (Main Orchestrator).
- `cpp/`: Source code C++ (Mouse Executor).
- `lib/`: Model YOLO dan Config.

## ⚡ Performance Tips (Khusus Laptop/RTX 3050)
1.  **WAJIB: LOCK FPS GAME!**
    *   **Masalah**: Jika FPS Game *Unlimited* (misal: 200 FPS), GPU akan dipakai 100% oleh game. AI tidak kebagian tenaga, menyebabkan lag parah (Inferensi 300ms+).
    *   **Solusi**: Batasi/Cap FPS Game di **60 - 90 FPS**. Ini memberi "napas" bagi GPU untuk menjalankan AI deteksi dengan super cepat.
2.  **Paksa Gunakan GPU Nvidia**:
    *   Buka **Windows Settings** -> **Display** -> **Graphics**.
    *   Cari/Browse `python.exe` (lokasi python kamu).
    *   Set ke **High Performance** (Nvidia RTX 3050).
    *   *Seringkali Python defaultnya jalan di iGPU (AMD Radeon/Intel) yang bikin FPS drop.*
2.  **Power Mode**: Pastikan laptop dicolok charger dan mode **Performance**.
3.  **DXCam**: Capturing di laptop kadang lebih lambat karena harus nyebrang dari iGPU ke dGPU (Optimus). Solusinya: mainkan game di **Windowed/Borderless**.

---
**Disclaimer**: Use at your own risk. For educational purposes only.
