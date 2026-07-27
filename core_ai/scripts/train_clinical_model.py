import os
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing import image_dataset_from_directory

# ==========================================
# HYPERPARAMETERS & CONFIG
# ==========================================
IMG_SIZE = (512, 512)
BATCH_SIZE = 16
EPOCHS = 20
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'train')
VAL_DIR = os.path.join(BASE_DIR, 'data', 'val')
MODEL_OUT_PATH = os.path.join(BASE_DIR, 'models', 'silicosis_model_v1.h5')

def train_model():
    print("==================================================")
    print(" MARUCURE: CLINICAL TRANSFER LEARNING PIPELINE")
    print("==================================================")
    
    if not os.path.exists(DATA_DIR):
        print(f"[ERROR] Data directory {DATA_DIR} does not exist.")
        print("Please place your images in data/train/normal/ and data/train/silicosis/")
        return

    # 1. Load Datasets with minimal preprocessing
    # Our JS UI sends pixels in [0, 1] range (division by 255 happens in app.js).
    # MobileNetV2 expects [-1, 1]. We will handle this in the model architecture.
    train_dataset = image_dataset_from_directory(
        DATA_DIR,
        shuffle=True,
        batch_size=BATCH_SIZE,
        image_size=IMG_SIZE,
        color_mode='rgb'
    )
    
    # Check if validation dir exists, otherwise split from train
    if os.path.exists(VAL_DIR) and len(os.listdir(VAL_DIR)) > 0:
        val_dataset = image_dataset_from_directory(
            VAL_DIR,
            shuffle=True,
            batch_size=BATCH_SIZE,
            image_size=IMG_SIZE,
            color_mode='rgb'
        )
    else:
        print("[INFO] No separate val folder found. Splitting from train dataset (80/20)...")
        train_dataset = image_dataset_from_directory(
            DATA_DIR,
            validation_split=0.2,
            subset="training",
            seed=123,
            shuffle=True,
            batch_size=BATCH_SIZE,
            image_size=IMG_SIZE,
            color_mode='rgb'
        )
        val_dataset = image_dataset_from_directory(
            DATA_DIR,
            validation_split=0.2,
            subset="validation",
            seed=123,
            shuffle=True,
            batch_size=BATCH_SIZE,
            image_size=IMG_SIZE,
            color_mode='rgb'
        )

    # Performance optimization
    AUTOTUNE = tf.data.AUTOTUNE
    train_dataset = train_dataset.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_dataset = val_dataset.cache().prefetch(buffer_size=AUTOTUNE)

    # 2. Data Augmentation (Crucial for small datasets to prevent overfitting)
    data_augmentation = tf.keras.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.05), # Slight 5-degree rotation
        layers.RandomZoom(0.1),      # 10% zoom
        layers.RandomContrast(0.1),
    ])

    # 3. Transfer Learning Architecture
    # Load MobileNetV2 without its top classification layer
    base_model = MobileNetV2(
        input_shape=IMG_SIZE + (3,),
        include_top=False,
        weights='imagenet'
    )
    
    # Freeze the base weights initially
    base_model.trainable = False

    # 4. Construct the Final Pipeline
    inputs = tf.keras.Input(shape=IMG_SIZE + (3,))
    
    # Note: Our app.js sends RGB floats in [0, 1] scale. 
    # MobileNetV2 requires pixels in [-1, 1] scale.
    # Therefore, we map [0, 1] to [-1, 1] -> (x * 2) - 1
    x = layers.Rescaling(2.0, offset=-1.0)(inputs)
    
    # Apply data augmentation only during training
    x = data_augmentation(x)
    
    # Pass through the frozen base model
    x = base_model(x, training=False)
    
    # Add a global spatial average pooling layer
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.2)(x)
    
    # Final dense layer for binary classification (0 = Normal, 1 = Silicosis)
    # Using sigmoid activation for probability percentage
    outputs = layers.Dense(1, activation='sigmoid')(x)
    
    model = tf.keras.Model(inputs, outputs)

    # 5. Compile the Model
    base_learning_rate = 0.0001
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=base_learning_rate),
        loss=tf.keras.losses.BinaryCrossentropy(),
        metrics=['accuracy', tf.keras.metrics.AUC()]
    )

    model.summary()

    # 6. Train the Model
    print("\n[INFO] Starting Phase 1: Training the custom Top Layers...")
    history = model.fit(
        train_dataset,
        epochs=EPOCHS,
        validation_data=val_dataset
    )
    
    # Optional: Phase 2 Fine Tuning (Unfreezing top layers of MobileNet)
    print("\n[INFO] Starting Phase 2: Fine-tuning deeper layers...")
    base_model.trainable = True
    fine_tune_at = 100
    for layer in base_model.layers[:fine_tune_at]:
        layer.trainable = False
        
    model.compile(
        optimizer=tf.keras.optimizers.RMSprop(learning_rate=base_learning_rate/10),
        loss=tf.keras.losses.BinaryCrossentropy(),
        metrics=['accuracy']
    )
    
    total_epochs = EPOCHS + 10
    history_fine = model.fit(
        train_dataset,
        epochs=total_epochs,
        initial_epoch=history.epoch[-1],
        validation_data=val_dataset
    )

    # 7. Save the H5 Model
    os.makedirs(os.path.dirname(MODEL_OUT_PATH), exist_ok=True)
    model.save(MODEL_OUT_PATH)
    print(f"\n[SUCCESS] Clinical Model successfully trained and saved to {MODEL_OUT_PATH}")
    print("Next Step: Run export_tflite.py to compress this model for the Edge AI Browser node.")

if __name__ == '__main__':
    train_model()
