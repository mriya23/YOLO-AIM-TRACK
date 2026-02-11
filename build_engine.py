
import os
import sys
import tensorrt as trt

# Paths
ONNX_FILE_PATH = "lib/best.onnx"
ENGINE_FILE_PATH = "lib/best.engine"

# Logger
TRT_LOGGER = trt.Logger(trt.Logger.WARNING)

def build_engine(onnx_file_path):
    print(f"TensorRT Version: {trt.__version__}")
    
    builder = trt.Builder(TRT_LOGGER)
    
    # Create network with explicit batch
    distinct_batch = 1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
    network = builder.create_network(distinct_batch)
    
    # Create parser
    parser = trt.OnnxParser(network, TRT_LOGGER)
    
    # Create config
    config = builder.create_builder_config()
    
    # Set memory pool limit (required for TRT 10+)
    # 2GB workspace (restored for optimal build)
    config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 1 << 31) 
    
    # Enable FP16 if supported
    if builder.platform_has_fast_fp16:
        print("Enabling FP16 mode")
        config.set_flag(trt.BuilderFlag.FP16)
    else:
        print("FP16 not supported, using FP32")
    
    # Parse ONNX
    print(f"Parsing ONNX file: {onnx_file_path}")
    with open(onnx_file_path, 'rb') as model:
        if not parser.parse(model.read()):
            print('ERROR: Failed to parse the ONNX file.')
            for error in range(parser.num_errors):
                print(parser.get_error(error))
            return None
    
    # Build engine
    print("Building serialized engine... (this may take a few minutes)")
    try:
        # TRT 8.5+ API
        serialized_engine = builder.build_serialized_network(network, config)
    except AttributeError:
        # Older TRT API fallback (just in case)
        engine = builder.build_engine(network, config)
        serialized_engine = engine.serialize() if engine else None
        
    return serialized_engine

if __name__ == "__main__":
    if not os.path.exists(ONNX_FILE_PATH):
        print(f"Error: {ONNX_FILE_PATH} not found.")
        sys.exit(1)
        
    engine_bytes = build_engine(ONNX_FILE_PATH)
    
    if engine_bytes:
        with open(ENGINE_FILE_PATH, "wb") as f:
            f.write(engine_bytes)
        print(f"Successfully saved engine to {ENGINE_FILE_PATH}")
    else:
        print("Failed to build engine.")
        sys.exit(1)
