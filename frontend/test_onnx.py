import os
import sys
from pathlib import Path

# Manually add the DLL directory – copy exactly what your __init__.py does
venv_root = Path(sys.executable).parent.parent
onnx_capi = venv_root / 'Lib' / 'site-packages' / 'onnxruntime' / 'capi'
print(f"capi exists? {onnx_capi.exists()}")
if onnx_capi.exists() and hasattr(os, 'add_dll_directory'):
    added = os.add_dll_directory(str(onnx_capi))
    print(f"Added DLL directory: {added}")

# Now try to import
print("Importing onnxruntime...")
import onnxruntime as onnxrt
print(f"SUCCESS! onnxruntime version: {onnxrt.__version__}")