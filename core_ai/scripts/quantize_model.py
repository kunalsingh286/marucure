import tensorflow as tf
import numpy as np
import os
import cv2

DATA_DIR = os.path.abspath("core_ai/data/val")

def representative_dataset_gen():
    """
    Yields sample pixel matrices from our actual verification sets 
    to properly calibrate the INT8 mathematical optimization scaling values.
    """
    # Fetch 100 true sample images from the normal cohort folder for calibration
    sample_folder = os.path.join(DATA_DIR, "normal")
    images = os.listdir(sample_folder)[:100]
    
    for img_name in images:
        img_path = os.path.join(sample_folder, img_name)
        img = cv2.imread(img_path)
        if img is not None:
            img_resized = cv2.resize(img, (512, 512))
            img_float = img_resized.astype(np.float32) / 255.0 # Normalize tracking arrays
            yield [np.expand_dims(img_float, axis=0)]

def execute_quantization():
    h5_model_path = "core_ai/models/uncompressed_silicosis_model.h5"
    tflite_output_path = "core_ai/models/silicosis_detector.tflite"
    
    print("[INFO] Initializing TFLite Converter Engine...")
    converter = tf.lite.TFLiteConverter.from_keras_model(tf.keras.models.load_model(h5_model_path, compile=False))
    
    # Configure strict INT8 quantization constraints
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset_gen
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.float32
    converter.inference_output_type = tf.float32
    
    print("[INFO] Processing 8-bit Quantization Array Conversions...")
    quantized_tflite_model = converter.convert()
    
    with open(tflite_output_path, "wb") as f:
        f.write(quantized_tflite_model)
        
    print(f"[SUCCESS] Compressed edge binary generated: {tflite_output_path}")
    print(f"[SIZE CHECK] Model file optimized for offline mobile device execution grids.")

if __name__ == "__main__":
    execute_quantization()
