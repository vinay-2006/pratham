"""
backend/app/ml/lab_model.py
============================
Singleton XGBoost cardiac risk model + SHAP explainer.

Loaded once at application startup (via get_lab_model()).
Never reloaded per-request.

Model: task9_xgboost_heart_model.json
Features (15, in exact order the model expects):
  Age, RestingBP, Cholesterol, FastingBS, MaxHR, Oldpeak,
  Sex_M,
  ChestPainType_ATA, ChestPainType_NAP, ChestPainType_TA,
  RestingECG_Normal, RestingECG_ST,
  ExerciseAngina_Y,
  ST_Slope_Flat, ST_Slope_Up

ASY (Asymptomatic) is the reference level for ChestPainType.
LVH (Left Ventricular Hypertrophy) is the reference level for RestingECG.
Down/Flat→Flat, Up→Up, Down is reference for ST_Slope.
Sex_F is the reference level.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ── Feature schema (must match training column order exactly) ─────────────

FEATURE_NAMES: list[str] = [
    "Age",
    "RestingBP",
    "Cholesterol",
    "FastingBS",
    "MaxHR",
    "Oldpeak",
    # One-hot encoded categoricals
    "Sex_M",
    "ChestPainType_ATA",
    "ChestPainType_NAP",
    "ChestPainType_TA",
    "RestingECG_Normal",
    "RestingECG_ST",
    "ExerciseAngina_Y",
    "ST_Slope_Flat",
    "ST_Slope_Up",
]

# ── Singleton holder ──────────────────────────────────────────────────────

class _LabModelSingleton:
    """Holds the loaded XGBoost model and SHAP explainer — one instance per process."""

    _model = None       # xgb.XGBClassifier
    _explainer = None   # shap.TreeExplainer
    _loaded: bool = False

    @classmethod
    def load(cls, model_path: Path) -> None:
        if cls._loaded:
            return
        try:
            import xgboost as xgb  # deferred import — optional dependency
            model = xgb.XGBClassifier()
            model.load_model(str(model_path))
            cls._model = model
            logger.info("[PRATHAM/ML] XGBoost model loaded from %s", model_path)
        except Exception as exc:
            logger.error("[PRATHAM/ML] Failed to load XGBoost model: %s", exc)
            raise RuntimeError(f"Cannot load XGBoost model: {exc}") from exc

        try:
            import shap
            cls._explainer = shap.TreeExplainer(cls._model)
            logger.info("[PRATHAM/ML] SHAP TreeExplainer initialised.")
        except ImportError:
            logger.warning(
                "[PRATHAM/ML] shap not installed — SHAP explanations will be empty. "
                "Run: pip install shap"
            )
            cls._explainer = None
        except Exception as exc:
            logger.warning("[PRATHAM/ML] SHAP explainer init failed (non-fatal): %s", exc)
            cls._explainer = None

        cls._loaded = True

    @classmethod
    def model(cls):
        return cls._model

    @classmethod
    def explainer(cls):
        return cls._explainer


# ── Public API ────────────────────────────────────────────────────────────

def _resolve_model_path() -> Path:
    """
    Locate the model JSON at backend/ml_models/task9_xgboost_heart_model.json.
    __file__ = .../backend/app/ml/lab_model.py
    parents[0] = ml/
    parents[1] = app/
    parents[2] = backend/    ← this is what we want
    """
    model_name = "task9_xgboost_heart_model.json"
    # Primary: relative to this file
    candidate = Path(__file__).resolve().parents[2] / "ml_models" / model_name
    if candidate.exists():
        return candidate
    # Fallback: walk up to find ml_models/
    for parent in Path(__file__).resolve().parents:
        alt = parent / "ml_models" / model_name
        if alt.exists():
            return alt
    return candidate  # will fail with a clear path in the error message


_MODEL_PATH = _resolve_model_path()


def load_lab_model() -> None:
    """Call once at startup (in FastAPI lifespan). Idempotent."""
    _LabModelSingleton.load(_MODEL_PATH)


def get_lab_model():
    """Return the loaded XGBClassifier. Raises if not loaded."""
    m = _LabModelSingleton.model()
    if m is None:
        raise RuntimeError("Lab model not loaded. Call load_lab_model() at startup first.")
    return m


def get_shap_explainer():
    """Return the SHAP explainer (may be None if shap not installed)."""
    return _LabModelSingleton.explainer()


# ── Preprocessing ─────────────────────────────────────────────────────────

def build_feature_vector(patient: dict[str, Any]) -> np.ndarray:
    """
    Convert raw patient dict → 15-feature numpy array matching training schema.

    Parameters (raw input keys accepted):
        age             int         Patient age in years
        sex             str         "M" or "F"
        chest_pain_type str         "ASY" | "ATA" | "NAP" | "TA"
        resting_bp      int/float   Resting blood pressure (mmHg)
        cholesterol     int/float   Serum cholesterol (mg/dL); 0 → treated as missing → 200 default
        fasting_bs      int         Fasting blood sugar >120 mg/dL → 1, else 0
        resting_ecg     str         "Normal" | "ST" | "LVH"
        max_hr          int/float   Maximum heart rate achieved
        exercise_angina str         "Y" or "N"
        oldpeak         float       ST depression induced by exercise vs rest
        st_slope        str         "Up" | "Flat" | "Down"

    Returns:
        np.ndarray of shape (1, 15) with float64 values.
    """
    age          = float(patient.get("age", 50))
    resting_bp   = float(patient.get("resting_bp", 120))
    cholesterol  = float(patient.get("cholesterol", 0))
    fasting_bs   = int(patient.get("fasting_bs", 0))
    max_hr       = float(patient.get("max_hr", 100))
    oldpeak      = float(patient.get("oldpeak", 0.0))

    # Cholesterol=0 in this dataset means "not measured" → impute with dataset mean (≈200)
    if cholesterol == 0:
        cholesterol = 200.0

    # One-hot: Sex
    sex = (patient.get("sex") or "M").upper()
    sex_m = 1 if sex == "M" else 0

    # One-hot: ChestPainType (reference = ASY)
    cpt = (patient.get("chest_pain_type") or "ASY").upper()
    cpt_ata = 1 if cpt == "ATA" else 0
    cpt_nap = 1 if cpt == "NAP" else 0
    cpt_ta  = 1 if cpt == "TA"  else 0

    # One-hot: RestingECG (reference = LVH)
    ecg = (patient.get("resting_ecg") or "Normal").strip()
    ecg_normal = 1 if ecg == "Normal" else 0
    ecg_st     = 1 if ecg == "ST"     else 0

    # One-hot: ExerciseAngina (reference = N)
    ea = (patient.get("exercise_angina") or "N").upper()
    ea_y = 1 if ea == "Y" else 0

    # One-hot: ST_Slope (reference = Down)
    slope = (patient.get("st_slope") or "Flat").strip().capitalize()
    slope_flat = 1 if slope == "Flat" else 0
    slope_up   = 1 if slope == "Up"   else 0

    vector = [
        age, resting_bp, cholesterol, fasting_bs, max_hr, oldpeak,
        sex_m,
        cpt_ata, cpt_nap, cpt_ta,
        ecg_normal, ecg_st,
        ea_y,
        slope_flat, slope_up,
    ]
    return np.array([vector], dtype=np.float64)


# ── Inference ─────────────────────────────────────────────────────────────

def run_inference(patient: dict[str, Any]) -> dict[str, Any]:
    """
    Full inference pipeline for one patient.

    Returns:
        {
            "risk_probability": float,     # 0.0–1.0
            "prediction":       str,       # "high_risk" | "low_risk"
            "shap_values":      dict,      # feature_name → shap_value (float)
            "input_features":   dict,      # feature_name → value used
        }
    """
    model = get_lab_model()
    X = build_feature_vector(patient)

    # Prediction
    proba   = float(model.predict_proba(X)[0][1])
    label   = "high_risk" if proba >= 0.5 else "low_risk"

    # Feature vector as a labelled dict for storage
    input_features = {name: float(X[0][i]) for i, name in enumerate(FEATURE_NAMES)}

    # SHAP
    shap_values: dict[str, float] = {}
    explainer = get_shap_explainer()
    if explainer is not None:
        try:
            sv = explainer.shap_values(X)
            # TreeExplainer on binary classifier returns (n_samples, n_features)
            if sv.ndim == 2:
                row = sv[0]
            else:
                row = sv[1][0] if isinstance(sv, list) else sv[0]
            shap_values = {name: round(float(row[i]), 6) for i, name in enumerate(FEATURE_NAMES)}
        except Exception as exc:
            logger.warning("[PRATHAM/ML] SHAP computation failed (non-fatal): %s", exc)

    return {
        "risk_probability": round(proba, 6),
        "prediction": label,
        "shap_values": shap_values,
        "input_features": input_features,
    }
