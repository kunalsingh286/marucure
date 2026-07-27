import cv2
import numpy as np
import tensorflow as tf
import os

class QAError(ValueError):
    """Exception raised for QA validation failures (e.g., blur, low contrast)."""
    pass

def verify_image_quality(image_path: str):
    """
    Reads the chest X-ray in grayscale, resizes it to 512x512 pixels,
    and dynamically evaluates the image contrast by calculating the matrix standard deviation.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")

    # Read image in grayscale
    gray_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if gray_image is None:
        raise ValueError(f"Could not read the image file as an image: {image_path}")

    # Resize to 512x512
    resized_img = cv2.resize(gray_image, (512, 512))
    
    # Calculate matrix standard deviation for contrast evaluation
    std_dev = np.std(resized_img)
    
    # Clinical threshold for acceptable contrast
    if std_dev < 15.0:
        raise QAError(f"Image contrast standard deviation ({std_dev:.2f}) is below the clinical threshold of 15.0. Image rejected.")
        
    return resized_img

def run_tflite_inference(tflite_path: str, image_path: str):
    """
    Runs the inference using the TFLite interpreter.
    """
    # Use standard tf.lite since tflite_runtime may not be available on all OS
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # QA Check - this throws if quality is bad
    verify_image_quality(image_path)
    
    # Preprocess for model (needs 3 channels, 512x512)
    bgr_img = cv2.imread(image_path)
    rgb_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
    resized_rgb = cv2.resize(rgb_img, (512, 512))
    
    # Scale to 0-1 and format for int8 quantization input type if required, 
    # but the model we compiled takes uint8 inputs.
    input_shape = input_details[0]['shape']
    input_dtype = input_details[0]['dtype']
    
    if input_dtype == np.uint8:
        # Scale 0-255 uint8 directly
        input_data = np.expand_dims(resized_rgb, axis=0).astype(np.uint8)
    else:
        # Float32 fallback
        input_data = (np.expand_dims(resized_rgb, axis=0) / 255.0).astype(np.float32)
        
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    
    output_data = interpreter.get_tensor(output_details[0]['index'])
    
    if output_details[0]['dtype'] == np.uint8:
        # De-quantize if necessary, for standard sigmoid, uint8 represents 0-255 -> 0.0-1.0
        # Wait, the quantization params have scale and zero_point
        scale, zero_point = output_details[0]['quantization']
        if scale > 0:
            score = (float(output_data[0][0]) - zero_point) * scale
        else:
            score = float(output_data[0][0]) / 255.0
    else:
        score = float(output_data[0][0])
        
    return score

def generate_gradcam_heatmap(keras_model_path: str, image_path: str, output_path: str):
    """
    Generates a normalized diagnostic visual output overlay (color gradient heatmap)
    pointing out exact structural lung-field densities, and saves the resulting visual artifact locally.
    
    Uses the full Keras model since TFLite does not preserve gradients or intermediate activations natively.
    """
    model = tf.keras.models.load_model(keras_model_path)
    
    # The base model was created with include_top=False, so its output IS the last conv layer.
    base_model = None
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model):
            base_model = layer
            break
            
    # Preprocess image
    bgr_img = cv2.imread(image_path)
    rgb_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
    resized_rgb = cv2.resize(rgb_img, (512, 512))
    img_array = (np.expand_dims(resized_rgb, axis=0) / 255.0).astype(np.float32)
    
    with tf.GradientTape() as tape:
        # Get the base features by running the base model directly
        last_conv_layer_output = base_model(img_array)
        tape.watch(last_conv_layer_output)
        
        # Apply the remaining classification layers
        x = last_conv_layer_output
        started = False
        for layer in model.layers:
            if started:
                x = layer(x)
            if layer.name == base_model.name:
                started = True
                
        preds = x
        # Assuming binary classification, get the prediction value
        class_channel = preds[:, 0]
        
    # Gradient of the output neuron with respect to the output feature map of the last conv layer
    grads = tape.gradient(class_channel, last_conv_layer_output)
    
    # Mean pooling the gradients over the spatial dimensions
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    
    # Multiply each channel in the feature map array by "how important this channel is"
    last_conv_layer_output = last_conv_layer_output.numpy()[0]
    pooled_grads = pooled_grads.numpy()
    
    for i in range(pooled_grads.shape[-1]):
        last_conv_layer_output[:, :, i] *= pooled_grads[i]
        
    # Heatmap is the mean of all channels
    heatmap = np.mean(last_conv_layer_output, axis=-1)
    
    # Normalize the heatmap between 0 and 1
    heatmap = np.maximum(heatmap, 0)
    heatmap_max = np.max(heatmap)
    if heatmap_max != 0:
        heatmap /= heatmap_max
        
    # Create the visual artifact overlay
    heatmap_uint8 = np.uint8(255 * heatmap)
    jet_heatmap = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    jet_heatmap = cv2.resize(jet_heatmap, (bgr_img.shape[1], bgr_img.shape[0]))
    
    superimposed_img = cv2.addWeighted(bgr_img, 0.6, jet_heatmap, 0.4, 0)
    
    cv2.imwrite(output_path, superimposed_img)
    return output_path
