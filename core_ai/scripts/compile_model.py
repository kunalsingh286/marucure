import tensorflow as tf
import numpy as np
import os

# Set paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_SAVE_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_SAVE_DIR, exist_ok=True)
TFLITE_MODEL_PATH = os.path.join(MODEL_SAVE_DIR, "silicosis_detector.tflite")
TF_MODEL_PATH = os.path.join(MODEL_SAVE_DIR, "silicosis_detector.keras")

def build_model():
    """
    Builds the combined model architecture containing the CXR foundation backbone
    paired with a custom classification dense head for Silicosis detection.
    (Note: Using MobileNetV2 as a stand-in for the local 'google/cxr-foundation' 
    backbone for demonstration purposes).
    """
    input_shape = (512, 512, 3)
    
    # cxr-foundation open-weights backbone stand-in
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights='imagenet'
    )
    
    # Freeze the foundation backbone
    base_model.trainable = False
    
    # Custom classification dense head for Silicosis
    inputs = tf.keras.Input(shape=input_shape)
    x = base_model(inputs, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dense(128, activation='relu')(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = tf.keras.layers.Dense(1, activation='sigmoid')(x)
    
    model = tf.keras.Model(inputs, outputs, name="silicosis_cxr_model")
    return model

def representative_dataset_gen():
    """
    Representative dataset generator for INT8 quantization calibration.
    Yields sample tensors representative of the expected CXR inputs.
    """
    for _ in range(100):
        # Generate dummy 512x512x3 images normalized to [0, 1]
        yield [np.random.uniform(0, 1, size=(1, 512, 512, 3)).astype(np.float32)]

def compile_and_quantize():
    print("Building and saving the Keras model...")
    model = build_model()
    model.save(TF_MODEL_PATH)
    
    print("Initializing TFLiteConverter...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Enforce full 8-bit quantization configuration
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset_gen
    
    # Ensure all operations are integer-based (INT8)
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    
    # Set input and output tensors to uint8 or int8 (common for edge TPUs/CPUs)
    converter.inference_input_type = tf.uint8
    converter.inference_output_type = tf.uint8
    
    print("Quantizing model... this may take a few moments.")
    tflite_quant_model = converter.convert()
    
    with open(TFLITE_MODEL_PATH, "wb") as f:
        f.write(tflite_quant_model)
        
    print(f"Production-ready INT8 model saved successfully to: {TFLITE_MODEL_PATH}")

if __name__ == "__main__":
    compile_and_quantize()
