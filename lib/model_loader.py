"""
Model Loader Module - AI Object Detection Model Integration
Handles loading best.pt (PyTorch) or best.engine (TensorRT) with validation and fallbacks.
Uses PyTorch for CUDA memory management to avoid external dependency issues.
"""
import os
import sys
import time
from typing import Optional, Tuple, List, Any

import cv2
import numpy as np

# Try importing ML frameworks
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[!] PyTorch not available")

try:
    import tensorrt as trt
    TRT_AVAILABLE = True
except ImportError:
    TRT_AVAILABLE = False

from termcolor import colored


class TensorRTModel:
    """TensorRT inference engine using PyTorch for memory management"""
    
    def __init__(self, engine_path: str):
        self.logger = trt.Logger(trt.Logger.INFO)
        with open(engine_path, "rb") as f, trt.Runtime(self.logger) as runtime:
            self.engine = runtime.deserialize_cuda_engine(f.read())
        
        self.context = self.engine.create_execution_context()
        
        # Allocate memory using PyTorch
        self.inputs = []
        self.outputs = []
        self.bindings = []
        
        # Dedicated stream for inference
        self.stream = torch.cuda.Stream()
        
        for i in range(self.engine.num_io_tensors):
            name = self.engine.get_tensor_name(i)
            # Get shape/dtype
            shape = self.engine.get_tensor_shape(name)
            # trt.nptype(dtype) gives numpy type
            dtype = trt.nptype(self.engine.get_tensor_dtype(name))
            
            # Create torch tensor on GPU
            # We use torch to manage device memory
            t_dtype = torch.from_numpy(np.array([], dtype=dtype)).dtype
            
            # Handle dynamic shapes if necessary (assuming fixed for now based on export)
            # If shape has -1, we might need a profile, but YOLO export usually is fixed size
            vol = 1
            for s in shape:
                vol *= abs(s)
            
            # Allocation
            device_tensor = torch.zeros(tuple(shape), dtype=t_dtype, device='cuda')
            
            binding = {
                'index': i,
                'name': name,
                'dtype': dtype,
                'shape': shape,
                'tensor': device_tensor,
                'ptr': device_tensor.data_ptr()
            }
            
            self.bindings.append(binding['ptr'])
            
            if self.engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT:
                self.inputs.append(binding)
            else:
                self.outputs.append(binding)

    def __call__(self, img: np.ndarray) -> List[np.ndarray]:
        """Run inference on image with GPU Preprocessing"""
        # 1. Resize on CPU (Fastest safe method for CV2 combatibility)
        # img is BGR uint8
        img_resized = cv2.resize(img, (320, 320))
        
        # 2. Upload to GPU immediately (uint8)
        # Create a view, don't copy yet if possible, but .cuda() will copy
        tensor_img = torch.from_numpy(img_resized).to(device='cuda', non_blocking=True)
        
        # 3. GPU Formatting: uint8 -> float32 -> /255 -> CHW -> Batch
        # This saves massive CPU cycles compared to numpy
        tensor_img = tensor_img.float().div(255.0).permute(2, 0, 1).unsqueeze(0)
        
        # 4. Copy to allocated TensorRT input buffer (GPU-GPU copy)
        self.inputs[0]['tensor'].copy_(tensor_img)
        
        # Set tensor addresses
        for i in range(len(self.inputs)):
            self.context.set_tensor_address(self.inputs[i]['name'], self.inputs[i]['ptr'])
        for i in range(len(self.outputs)):
            self.context.set_tensor_address(self.outputs[i]['name'], self.outputs[i]['ptr'])
        
        # Execute async
        self.context.execute_async_v3(stream_handle=self.stream.cuda_stream)
        
        # Synchronize
        self.stream.synchronize()
        
        # Copy output back (Device -> Host)
        results = []
        for out in self.outputs:
            results.append(out['tensor'].cpu().numpy())
            
        return results

    def half(self):
        """Compatibility method"""
        pass


class PyTorchModel:
    """PyTorch YOLOv5 model wrapper"""
    
    def __init__(self, model_path: str, use_cuda: bool = True):
        # Patch for PyTorch 1.11+ compatibility with legacy models
        import torch.nn as nn
        
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', 
                                     path=model_path, force_reload=False)
        
        # Apply patch to loaded model
        for m in self.model.modules():
            if isinstance(m, nn.Upsample):
                m.recompute_scale_factor = None
        
        if use_cuda and torch.cuda.is_available():
            self.model.cuda()
            self.model.half()  # FP16 for faster inference
            print(colored("[+] CUDA + FP16 Mode ENABLED", "green"))
        
        # Detection settings
        self.model.conf = 0.40
        self.model.iou = 0.45
        
    def __call__(self, img: np.ndarray):
        """Run inference and return results"""
        return self.model(img)
    
    def half(self):
        """Enable FP16 mode"""
        if torch.cuda.is_available():
            self.model.half()


class ModelLoader:
    """
    Unified model loader with automatic backend selection.
    Prioritizes TensorRT > PyTorch CUDA > PyTorch CPU
    """
    
    def __init__(self, model_dir: str = "lib"):
        self.model_dir = model_dir
        self.model = None
        self.backend = None
        self.input_size = (320, 320)
        self.performance_stats = {
            "total_inferences": 0,
            "total_time": 0,
            "avg_fps": 0
        }
        
    def load(self) -> bool:
        """
        Load the best available model.
        Returns True if successful, False otherwise.
        """
        engine_path = os.path.join(self.model_dir, "best.engine")
        pt_path = os.path.join(self.model_dir, "best.pt")
        
        # Try TensorRT first (fastest)
        if TRT_AVAILABLE and os.path.exists(engine_path):
            try:
                print(colored(f"[+] Loading TensorRT Engine: {engine_path}", "cyan"))
                self.model = TensorRTModel(engine_path)
                self.backend = "TensorRT"
                print(colored("[+] TensorRT Engine LOADED - Maximum Performance", "green"))
                return True
            except Exception as e:
                print(colored(f"[!] TensorRT load failed: {e}", "yellow"))
                import traceback
                traceback.print_exc()
        
        # Fallback to PyTorch
        if TORCH_AVAILABLE and os.path.exists(pt_path):
            try:
                print(colored(f"[+] Loading PyTorch Model: {pt_path}", "cyan"))
                use_cuda = torch.cuda.is_available()
                self.model = PyTorchModel(pt_path, use_cuda)
                self.backend = "PyTorch-CUDA" if use_cuda else "PyTorch-CPU"
                print(colored(f"[+] PyTorch Model LOADED - Backend: {self.backend}", "green"))
                return True
            except Exception as e:
                print(colored(f"[!] PyTorch load failed: {e}", "red"))
        
        print(colored("[X] No valid model found!", "red"))
        return False
    
    def validate(self) -> bool:
        """Validate model is working with a test inference"""
        if self.model is None:
            return False
            
        try:
            # Create dummy image for test
            test_img = np.zeros((320, 320, 3), dtype=np.uint8)
            _ = self.infer(test_img)
            print(colored("[+] Model validation PASSED", "green"))
            return True
        except Exception as e:
            print(colored(f"[X] Model validation FAILED: {e}", "red"))
            import traceback
            traceback.print_exc()
            return False
    
    def infer(self, frame: np.ndarray, conf_threshold: float = 0.45) -> List[List]:
        """
        Run inference on frame and return detections.
        
        Args:
            frame: BGR image array
            conf_threshold: Minimum confidence threshold
            
        Returns:
            List of detections: [[x1, y1, x2, y2, confidence], ...]
        """
        start_time = time.perf_counter()
        
        if self.backend == "TensorRT":
            # TensorRT inference
            raw_results = self.model(frame)
            num_cols = 6  # [x, y, w, h, conf, class]
            output = raw_results[0].reshape(-1, num_cols)
            valid = output[output[:, 4] > conf_threshold]
            
            # Scale factor for ROI: 320x320 input -> Frame input
            scale_x = frame.shape[1] / 320.0
            scale_y = frame.shape[0] / 320.0
            
            detections = []
            for row in valid:
                box = row[:4]
                conf = row[4]
                x1 = int((box[0] - box[2]/2) * scale_x)
                y1 = int((box[1] - box[3]/2) * scale_y)
                x2 = int((box[0] + box[2]/2) * scale_x)
                y2 = int((box[1] + box[3]/2) * scale_y)
                detections.append([x1, y1, x2, y2, conf])
        else:
            # PyTorch inference
            results = self.model(frame)
            detections = []
            if len(results.xyxy[0]) > 0:
                for *box, conf, cls in results.xyxy[0]:
                    if conf > conf_threshold:
                        detections.append([int(box[0]), int(box[1]), 
                                          int(box[2]), int(box[3]), conf.item()])
        
        # Update stats
        elapsed = time.perf_counter() - start_time
        self.performance_stats["total_inferences"] += 1
        self.performance_stats["total_time"] += elapsed
        self.performance_stats["avg_fps"] = (
            self.performance_stats["total_inferences"] / 
            self.performance_stats["total_time"]
        )
        
        return detections
    
    def get_stats(self) -> dict:
        """Get performance statistics"""
        return self.performance_stats.copy()


# Singleton instance
_loader: Optional[ModelLoader] = None

def get_model_loader(model_dir: str = "lib") -> ModelLoader:
    """Get or create model loader singleton"""
    global _loader
    if _loader is None:
        _loader = ModelLoader(model_dir)
    return _loader
