import os
import cv2
import numpy as np
import pytest
from core_ai.scripts.compile_model import compile_and_quantize, TFLITE_MODEL_PATH, TF_MODEL_PATH
from core_ai.scripts.inference_engine import verify_image_quality, run_tflite_inference, generate_gradcam_heatmap, QAError

# Fixtures for paths
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
GOOD_IMG_PATH = os.path.join(TEST_DIR, "test_good_cxr.png")
BAD_IMG_PATH = os.path.join(TEST_DIR, "test_bad_cxr.png")
HEATMAP_PATH = os.path.join(TEST_DIR, "test_heatmap.png")

def setup_module(module):
    """Setup dummy images for testing."""
    # Create a high contrast image (e.g., checkerboard or noise)
    good_img = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
    # Ensure high std dev by adding distinct blocks
    good_img[0:256, 0:256] = 0
    good_img[256:512, 256:512] = 255
    cv2.imwrite(GOOD_IMG_PATH, good_img)

    # Create a low contrast image (e.g., almost uniform grey)
    bad_img = np.full((512, 512, 3), 128, dtype=np.uint8)
    cv2.imwrite(BAD_IMG_PATH, bad_img)
    
    # Ensure models are compiled
    if not os.path.exists(TFLITE_MODEL_PATH):
        compile_and_quantize()

def teardown_module(module):
    """Cleanup dummy files."""
    for path in [GOOD_IMG_PATH, BAD_IMG_PATH, HEATMAP_PATH]:
        if os.path.exists(path):
            os.remove(path)

def test_verify_image_quality_success():
    """Verify that a high contrast image passes the QA check."""
    # Should not raise an exception
    resized = verify_image_quality(GOOD_IMG_PATH)
    assert resized.shape == (512, 512)

def test_verify_image_quality_failure():
    """Verify that a low contrast image raises a QAError."""
    with pytest.raises(QAError):
        verify_image_quality(BAD_IMG_PATH)

def test_tflite_inference():
    """Verify that the compiled TFLite model handles valid tensors and returns a score."""
    score = run_tflite_inference(TFLITE_MODEL_PATH, GOOD_IMG_PATH)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0

def test_gradcam_heatmap():
    """Verify that the Grad-CAM utility outputs a physical heatmap image."""
    output_path = generate_gradcam_heatmap(TF_MODEL_PATH, GOOD_IMG_PATH, HEATMAP_PATH)
    assert os.path.exists(output_path)
    
    # Verify the image is valid and has dimensions
    heatmap_img = cv2.imread(output_path)
    assert heatmap_img is not None
    assert heatmap_img.shape == (512, 512, 3)
