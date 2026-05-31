"""
Imaging Service — Stub for medical image analysis.

TODO: Integrate CheXNet or custom PyTorch CXR model from ml_models/.
"""

from __future__ import annotations


class ImagingService:
    """Analyses medical images and returns structured findings."""

    async def analyse_xray(
        self,
        image_url: str | None,
        clinical_context: str | None,
    ) -> dict[str, object]:
        """
        Stub: Run inference on a chest X-ray image.

        Args:
            image_url: URL to the uploaded image, or None for stub.
            clinical_context: Optional free-text clinical context.

        Returns:
            Dictionary with findings, impression, and confidence score.
        """
        # TODO: Download image, preprocess, run model inference
        return {
            "findings": [],
            "impression": "Stub: No model loaded.",
            "confidence": 0.0,
        }
