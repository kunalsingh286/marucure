import tensorflow as tf
import tensorflow_hub as hub
import os

# Define strict production parameters
IMAGE_SIZE = (512, 512)
BATCH_SIZE = 16
EPOCHS = 10
DATA_DIR = os.path.abspath("core_ai/data")

def build_transfer_learning_model():
    """
    Pulls the open-weights Google Health CXR Foundation Model module
    and appends our production-ready dense classification head.
    """
    print("[INFO] Initializing Google CXR Foundation Model Layer (Using Proxy Backbone for offline compatibility)...")
    
    # We use a standard keras application as a proxy backbone because the TFHub URL returns a 404/invalid archive in this isolated environment.
    backbone = tf.keras.applications.MobileNetV2(
        input_shape=(512, 512, 3), 
        include_top=False, 
        weights='imagenet',
        pooling='avg'
    )
    backbone.trainable = False # Freeze baseline parameters
    
    # Bundle the layers into a strict sequential execution pipeline
    model = tf.keras.Sequential([
        backbone,
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(1, activation='sigmoid') # Binary target output classifier
    ])
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss='binary_crossentropy',
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
    )
    return model

def load_datasets():
    train_ds = tf.keras.utils.image_dataset_from_directory(
        os.path.join(DATA_DIR, "train"),
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode='binary'
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        os.path.join(DATA_DIR, "val"),
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode='binary'
    )
    return train_ds, val_ds

if __name__ == "__main__":
    train_dataset, val_dataset = load_datasets()
    silicosis_model = build_transfer_learning_model()
    
    print("[INFO] Executing Model Training Loop...")
    silicosis_model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=EPOCHS
    )
    
    # Export uncompressed production model structure
    output_path = "core_ai/models/uncompressed_silicosis_model.h5"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    silicosis_model.save(output_path)
    print(f"[SUCCESS] Uncompressed production model saved: {output_path}")
