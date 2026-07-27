import os
import tensorflow as tf

# ==========================================
# HYPERPARAMETERS & CONFIG
# ==========================================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODEL_IN_PATH = os.path.join(BASE_DIR, 'models', 'silicosis_model_v1.h5')

# We export directly into the public web app directory
WEB_APP_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'public', 'app', 'assets', 'models'))
MODEL_OUT_PATH = os.path.join(WEB_APP_DIR, 'model_silicosis.tflite')

def export_tflite():
    print("==================================================")
    print(" MARUCURE: TFLITE EDGE QUANTIZATION")
    print("==================================================")
    
    if not os.path.exists(MODEL_IN_PATH):
        print(f"[ERROR] Trained model not found at {MODEL_IN_PATH}")
        print("Please run train_clinical_model.py first.")
        return

    print(f"[INFO] Loading Keras model from {MODEL_IN_PATH}...")
    model = tf.keras.models.load_model(MODEL_IN_PATH)
    
    print("[INFO] Initializing TFLiteConverter...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Enable Post-Training Quantization to drastically reduce file size
    print("[INFO] Applying INT8 / Float16 Quantization optimizations...")
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    # Note: For strict INT8, a representative dataset generator is needed.
    # We will use dynamic range quantization (hybrid Float16/INT8) which works beautifully 
    # out of the box and is extremely fast on browser WASM backends.
    
    print("[INFO] Converting model...")
    tflite_model = converter.convert()
    
    os.makedirs(WEB_APP_DIR, exist_ok=True)
    
    with open(MODEL_OUT_PATH, 'wb') as f:
        f.write(tflite_model)
        
    # Calculate compression ratio
    original_size = os.path.getsize(MODEL_IN_PATH) / (1024 * 1024)
    new_size = os.path.getsize(MODEL_OUT_PATH) / (1024 * 1024)
    
    print(f"\n[SUCCESS] TFLite Model Exported Successfully!")
    print(f"Export Path: {MODEL_OUT_PATH}")
    print(f"Original Size: {original_size:.2f} MB")
    print(f"Compressed Size: {new_size:.2f} MB ({(1 - (new_size/original_size))*100:.1f}% reduction)")
    print("\nYour MaruCure Offline PWA is now equipped with a real, clinical Edge AI Neural Network.")

if __name__ == '__main__':
    export_tflite()
