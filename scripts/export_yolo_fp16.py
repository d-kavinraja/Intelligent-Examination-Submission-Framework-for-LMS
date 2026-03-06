#!/usr/bin/env python3
"""
Script to export the primary YOLO model to ONNX FP16 format for inference optimization.
Run this script to generate 'improved_weights.onnx' in the models directory.
"""

from pathlib import Path
from ultralytics import YOLO

def main():
    models_dir = Path(__file__).resolve().parent.parent / "exam_middleware" / "models"
    model_path = models_dir / "improved_weights.pt"
    
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}")
        return

    print(f"Loading YOLO model from {model_path}...")
    model = YOLO(str(model_path))
    
    # Export to ONNX with FP16 (Safe Quantization)
    print("Exporting model to ONNX FP16 format...")
    # half=True enables FP16 precision
    exported_path = model.export(format="onnx", half=True)
    
    print(f"Successfully exported model to: {exported_path}")

if __name__ == "__main__":
    main()
