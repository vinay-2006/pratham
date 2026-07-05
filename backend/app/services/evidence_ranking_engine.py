"""
evidence_ranking_engine.py — Evidence Ranking Engine

Loads versioned YAML disease definitions from backend/app/knowledge_base/
and evaluates disease rules against clinical findings and patterns.
Computes deterministic support_score, conflict_score, and missing_evidence_score for every condition.
"""

from __future__ import annotations
import os
import glob
from typing import Any, Dict, List

# Lightweight fallback parser for simple YAML structures if PyYAML is not installed
def _load_yaml_dict(filepath: str) -> Dict[str, Any]:
    try:
        import yaml
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # Fallback basic loader for key-value / lists
        result: Dict[str, Any] = {}
        curr_key = None
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                sline = line.strip()
                if not sline or sline.startswith("#"):
                    continue
                if ":" in sline and not sline.startswith("-"):
                    parts = sline.split(":", 1)
                    curr_key = parts[0].strip()
                    val = parts[1].strip().strip('"').strip("'")
                    if val:
                        result[curr_key] = val
                    else:
                        result[curr_key] = []
                elif sline.startswith("- ") and curr_key:
                    item = sline[2:].strip().strip('"').strip("'")
                    if isinstance(result[curr_key], list):
                        result[curr_key].append(item)
        return result


def rank_evidence_for_conditions(
    vitals: Dict[str, Any],
    symptoms: Dict[str, Any] | List[str],
    clinical_patterns: List[Dict[str, Any]],
    lab_evaluations: List[Dict[str, Any]] | None = None,
    imaging_data: Dict[str, Any] | None = None,
    nlp_flags: Dict[str, Any] | None = None,
    kb_dir: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Evaluates all conditions in the Knowledge Base and ranks them by evidence score.
    Returns a sorted list of condition evaluations.
    """
    if kb_dir is None:
        kb_dir = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")

    sym_dict = symptoms if isinstance(symptoms, dict) else {s: True for s in symptoms}
    nlp = nlp_flags or {}
    labs = {item["analyte_key"]: item for item in (lab_evaluations or []) if "analyte_key" in item}
    active_pattern_keys = [p["pattern_key"] for p in clinical_patterns]

    yaml_files = glob.glob(os.path.join(kb_dir, "*.yaml"))
    results: List[Dict[str, Any]] = []

    for yfile in yaml_files:
        rule = _load_yaml_dict(yfile)
        if not rule or "condition_key" not in rule:
            continue

        c_key = rule["condition_key"]
        c_name = rule.get("condition_name", c_key.upper())
        version = str(rule.get("version", "1.0"))

        support_score = 0.0
        conflict_score = 0.0
        missing_score = 0.0

        matched_supporting: List[str] = []
        matched_conflicting: List[str] = []

        # 1. Evaluate supporting patterns
        for pat in rule.get("supporting_patterns", []):
            if pat in active_pattern_keys:
                support_score += 25.0
                matched_supporting.append(f"Clinical pattern matched: {pat.replace('_', ' ').title()}")

        # 2. Evaluate supporting findings (symptoms)
        supp_findings = rule.get("supporting_findings", {})
        if isinstance(supp_findings, dict):
            for sym in supp_findings.get("symptoms", []):
                if sym_dict.get(sym):
                    support_score += 20.0
                    matched_supporting.append(f"Symptom present: {sym.replace('_', ' ').title()}")

            # Supporting labs
            for l_rule in supp_findings.get("labs", []):
                if isinstance(l_rule, dict):
                    an = l_rule.get("analyte")
                    stat = l_rule.get("status")
                    if an in labs and labs[an]["status"] == stat:
                        support_score += 25.0
                        matched_supporting.append(f"Lab finding: {labs[an]['analyte']} is {stat}")

            # Supporting imaging
            supp_img = supp_findings.get("imaging", {})
            if isinstance(supp_img, dict) and imaging_data:
                pred = supp_img.get("prediction")
                if pred and (imaging_data.get("prediction") or "").lower() == pred.lower():
                    support_score += 30.0
                    matched_supporting.append(f"Imaging finding matches {pred}")

        # 3. Evaluate conflicting findings
        conf_findings = rule.get("conflicting_findings", {})
        if isinstance(conf_findings, dict):
            for sym in conf_findings.get("symptoms", []):
                if sym_dict.get(sym):
                    conflict_score += 15.0
                    matched_conflicting.append(f"Conflicting symptom: {sym.replace('_', ' ').title()}")

            for l_rule in conf_findings.get("labs", []):
                if isinstance(l_rule, dict):
                    an = l_rule.get("analyte")
                    stat = l_rule.get("status")
                    if an in labs and labs[an]["status"] == stat:
                        conflict_score += 20.0
                        matched_conflicting.append(f"Conflicting lab: {an.upper()} is {stat}")

        # Cap support score at 100
        support_score = min(100.0, support_score)

        # Missing evidence score penalty
        if not imaging_data and "imaging" in str(supp_findings):
            missing_score += 15.0
        if not labs and "labs" in str(supp_findings):
            missing_score += 15.0

        final_evidence_score = max(0.0, round(support_score - conflict_score - (0.5 * missing_score), 1))

        results.append({
            "condition_key": c_key,
            "condition_name": c_name,
            "evidence_score": final_evidence_score,
            "support_score": round(support_score, 1),
            "conflict_score": round(conflict_score, 1),
            "missing_evidence_score": round(missing_score, 1),
            "knowledge_base_version": version,
            "matched_supporting": matched_supporting,
            "matched_conflicting": matched_conflicting,
            "monitoring_priorities": rule.get("monitoring_priorities", []),
            "clinical_precautions": rule.get("clinical_precautions", []),
            "suggested_investigations": rule.get("suggested_investigations", []),
        })

    # Sort conditions by final evidence score descending
    results.sort(key=lambda x: x["evidence_score"], reverse=True)
    return results
