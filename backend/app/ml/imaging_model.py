"""
backend/app/ml/imaging_model.py
================================
Singleton EfficientNetB0 pneumonia classification model.

Loaded once at application startup (via load_imaging_model()).
Never reloaded per-request. Thread-safe singleton access.

Model: task10_efficientnetb0_pneumonia.keras

IMPORTANT: The model already contains EfficientNet preprocessing layers.
DO NOT divide pixels by 255 or apply any extra normalisation.
Feed raw pixel values directly from tf.keras.utils.img_to_array().
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────

MODEL_NAME = "task10_efficientnetb0_pneumonia"
MODEL_FILENAME = "task10_efficientnetb0_pneumonia.keras"
PREDICTION_THRESHOLD = 0.5
TARGET_SIZE = (224, 224)  # EfficientNetB0 default input size


# ── Singleton holder ──────────────────────────────────────────────────────

class _ImagingModelSingleton:
    """Holds the loaded Keras model — one instance per process."""

    _model = None
    _loaded: bool = False

    @classmethod
    def load(cls, model_path: Path) -> None:
        if cls._loaded:
            return
        try:
            import tensorflow as tf  # deferred import — heavy dependency
            cls._model = tf.keras.models.load_model(str(model_path))
            logger.info("[PRATHAM/ML] EfficientNetB0 imaging model loaded from %s", model_path)
        except Exception as exc:
            logger.error("[PRATHAM/ML] Failed to load imaging model: %s", exc)
            raise RuntimeError(f"Cannot load imaging model: {exc}") from exc

        cls._loaded = True

    @classmethod
    def model(cls):
        return cls._model


# ── Path resolution ───────────────────────────────────────────────────────

def _resolve_model_path() -> Path:
    """
    Locate the model at backend/ml_models/task10_efficientnetb0_pneumonia.keras.

    __file__ = .../backend/app/ml/imaging_model.py
    parents[0] = ml/
    parents[1] = app/
    parents[2] = backend/    ← this is what we want
    """
    # Primary: relative to this file
    candidate = Path(__file__).resolve().parents[2] / "ml_models" / MODEL_FILENAME
    if candidate.exists():
        return candidate
    # Fallback: walk up to find ml_models/
    for parent in Path(__file__).resolve().parents:
        alt = parent / "ml_models" / MODEL_FILENAME
        if alt.exists():
            return alt
    return candidate  # will fail with a clear path in the error message


_MODEL_PATH = _resolve_model_path()


# ── Public API ────────────────────────────────────────────────────────────

def load_imaging_model() -> None:
    """Call once at startup (in FastAPI lifespan). Idempotent."""
    if not _MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Imaging model not found at {_MODEL_PATH}. "
            f"Ensure {MODEL_FILENAME} is in the ml_models/ directory."
        )
    _ImagingModelSingleton.load(_MODEL_PATH)


def get_imaging_model():
    """Return the loaded Keras model. Raises if not loaded."""
    m = _ImagingModelSingleton.model()
    if m is None:
        raise RuntimeError("Imaging model not loaded. Call load_imaging_model() at startup first.")
    return m


def run_imaging_inference(image_path: str) -> dict[str, Any]:
    """
    Run pneumonia classification on a single chest X-ray image.

    IMPORTANT: The model has built-in EfficientNet preprocessing layers.
    Raw pixel values are fed directly — NO division by 255.

    Parameters:
        image_path: Absolute file path to the X-ray image (JPEG/PNG).

    Returns:
        {
            "pneumonia_probability": float,   # 0.0–1.0
            "prediction": "pneumonia" | "normal",
            "confidence": float,              # max(prob, 1-prob)
        }
    """
    import tensorflow as tf
    import numpy as np

    model = get_imaging_model()

    # Load image at EfficientNetB0's expected 224×224 size
    img = tf.keras.utils.load_img(image_path, target_size=TARGET_SIZE)
    arr = tf.keras.utils.img_to_array(img)  # shape: (224, 224, 3), raw pixels

    # DO NOT normalise — the model has built-in preprocessing layers
    batch = np.expand_dims(arr, axis=0)  # shape: (1, 224, 224, 3)

    # Predict
    raw_output = model.predict(batch, verbose=0)
    probability = float(raw_output[0][0])

    # Classify
    prediction = "pneumonia" if probability >= PREDICTION_THRESHOLD else "normal"
    confidence = max(probability, 1.0 - probability)

    return {
        "pneumonia_probability": round(probability, 6),
        "prediction": prediction,
        "confidence": round(confidence, 6),
    }


def generate_gradcam(image_path: str, output_path: str) -> str:
    """
    Generate a Grad-CAM heatmap overlay for a chest X-ray image.

    Uses TensorFlow GradientTape on the last convolutional layer
    of EfficientNetB0 to produce a class activation map.

    Parameters:
        image_path: Absolute path to the input X-ray image.
        output_path: Absolute path to save the heatmap overlay PNG.

    Returns:
        The output_path if successful, empty string if failed.
    """
    try:
        import tensorflow as tf
        import numpy as np

        model = get_imaging_model()

        # Load and preprocess image
        img = tf.keras.utils.load_img(image_path, target_size=TARGET_SIZE)
        arr = tf.keras.utils.img_to_array(img)
        batch = np.expand_dims(arr, axis=0)

        # Find the last convolutional layer
        last_conv_layer = None
        for layer in reversed(model.layers):
            if isinstance(layer, tf.keras.layers.Conv2D):
                last_conv_layer = layer
                break
            # Also check inside nested models (e.g. functional EfficientNet)
            if hasattr(layer, 'layers'):
                for sub_layer in reversed(layer.layers):
                    if isinstance(sub_layer, tf.keras.layers.Conv2D):
                        last_conv_layer = sub_layer
                        break
                if last_conv_layer:
                    break

        if last_conv_layer is None:
            logger.warning("[PRATHAM/ML] No Conv2D layer found — cannot generate Grad-CAM")
            return ""

        # Build a sub-model that outputs conv features + final prediction
        grad_model = tf.keras.Model(
            inputs=model.input,
            outputs=[last_conv_layer.output, model.output]
        )

        # Compute gradients
        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(batch)
            loss = predictions[:, 0]  # pneumonia probability

        grads = tape.gradient(loss, conv_outputs)
        if grads is None:
            logger.warning("[PRATHAM/ML] Gradient is None — Grad-CAM failed")
            return ""

        # Global average pooling of gradients
        weights = tf.reduce_mean(grads, axis=(0, 1, 2))
        cam = tf.reduce_sum(tf.multiply(conv_outputs[0], weights), axis=-1)

        # ReLU + normalize
        cam = tf.maximum(cam, 0)
        cam_max = tf.reduce_max(cam)
        if cam_max > 0:
            cam = cam / cam_max
        cam = cam.numpy()

        # Resize to original image dimensions
        import cv2
        heatmap = cv2.resize(cam, (TARGET_SIZE[1], TARGET_SIZE[0]))
        heatmap = np.uint8(255 * heatmap)
        heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

        # Overlay on original image
        original = cv2.resize(
            cv2.imread(image_path),
            (TARGET_SIZE[1], TARGET_SIZE[0])
        )
        if original is None:
            logger.warning("[PRATHAM/ML] Could not read original image for overlay")
            return ""

        overlay = cv2.addWeighted(original, 0.6, heatmap_color, 0.4, 0)
        cv2.imwrite(output_path, overlay)

        logger.info("[PRATHAM/ML] Grad-CAM heatmap saved to %s", output_path)
        return output_path

    except ImportError:
        logger.warning("[PRATHAM/ML] cv2 not installed — Grad-CAM overlay skipped")
        return ""
    except Exception as exc:
        logger.warning("[PRATHAM/ML] Grad-CAM generation failed (non-fatal): %s", exc)
        return ""

