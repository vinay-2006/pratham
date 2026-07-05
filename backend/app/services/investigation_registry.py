"""
Central Investigation Registry — maps canonical investigation names to supported analysis types and resolves aliases.
"""

from __future__ import annotations

# Canonical name -> analysis type ('imaging', 'lab', etc)
# If not present in this dictionary, the investigation does not support AI analysis in this version.
SUPPORTED_ANALYSES: dict[str, str] = {
    "Chest X-ray": "imaging",
    "CT Brain": "imaging",
    "CT Chest": "imaging",
    "Echocardiogram": "imaging",
    "FAST Ultrasound": "imaging",
    "CBC": "lab",
    "Basic Metabolic Panel": "lab",
    "Urinalysis": "lab",
    "Blood Glucose": "lab",
    "Troponin": "lab",
    "ABG": "lab",
    "D-Dimer": "lab",
    "Cardiac Enzymes": "lab",
    "Coagulation Profile": "lab",
    "Blood Group & Cross-match": "lab",
    "Electrolytes": "lab",
}

# Alias -> canonical name
ALIASES: dict[str, str] = {
    # CBC
    "cbc": "CBC",
    "complete blood count": "CBC",
    "full blood count": "CBC",
    "fbc": "CBC",
    
    # Chest X-ray
    "chest xray": "Chest X-ray",
    "chest x-ray": "Chest X-ray",
    "chest x ray": "Chest X-ray",
    "chest radiograph": "Chest X-ray",
    "cxr": "Chest X-ray",
    "x-ray": "Chest X-ray",
    "xray": "Chest X-ray",
    
    # BMP
    "bmp": "Basic Metabolic Panel",
    "basic metabolic panel": "Basic Metabolic Panel",
    
    # Urinalysis
    "urinalysis": "Urinalysis",
    "urine analysis": "Urinalysis",
    "ua": "Urinalysis",
    
    # Blood Glucose
    "blood sugar": "Blood Glucose",
    "blood glucose": "Blood Glucose",
    "rbs": "Blood Glucose",
    "fbs": "Blood Glucose",
    
    # CT Brain
    "ct brain": "CT Brain",
    "ct head": "CT Brain",
    
    # MRI Brain
    "mri brain": "MRI Brain",
    "mri head": "MRI Brain",
    "mri": "MRI Brain",
    
    # CT Chest
    "ct chest": "CT Chest",
    
    # Echocardiogram
    "echo": "Echocardiogram",
    "echocardiogram": "Echocardiogram",
    
    # FAST Ultrasound
    "fast scan": "FAST Ultrasound",
    "fast ultrasound": "FAST Ultrasound",
    "fast": "FAST Ultrasound",
    
    # Troponin
    "troponin": "Troponin",
    "trop": "Troponin",
    
    # ABG
    "abg": "ABG",
    "arterial blood gas": "ABG",
    
    # D-Dimer
    "d-dimer": "D-Dimer",
    "d dimer": "D-Dimer",
    
    # Cardiac Enzymes
    "cardiac enzymes": "Cardiac Enzymes",
    
    # Coagulation
    "coagulation profile": "Coagulation Profile",
    "coagulation": "Coagulation Profile",
    "coag": "Coagulation Profile",
    
    # Blood Group & Cross-match
    "blood group": "Blood Group & Cross-match",
    "crossmatch": "Blood Group & Cross-match",
    "blood group & cross-match": "Blood Group & Cross-match",
    "blood group and crossmatch": "Blood Group & Cross-match",
    
    # Electrolytes
    "electrolytes": "Electrolytes",
    "serum electrolytes": "Electrolytes",
}

def normalize_investigation_name(raw: str) -> str:
    """
    Normalizes an entered investigation name by resolving aliases and canonicalizing spelling.
    If the name is not in our known aliases/canonical registry, it returns the trimmed, title-cased string.
    """
    cleaned = " ".join(raw.strip().split())
    lower = cleaned.lower()
    
    if lower in ALIASES:
        return ALIASES[lower]
        
    # Check case-insensitive match against canonical keys
    for canonical in SUPPORTED_ANALYSES:
        if canonical.lower() == lower:
            return canonical
            
    # Try title casing
    return cleaned.title()

def get_analysis_type(canonical_name: str) -> str | None:
    """
    Returns the supported analysis type ('imaging', 'lab') or None if not supported by AI.
    """
    return SUPPORTED_ANALYSES.get(canonical_name)

def is_analysis_supported(canonical_name: str) -> bool:
    """
    Returns True if AI analysis is supported for this investigation.
    """
    return canonical_name in SUPPORTED_ANALYSES
