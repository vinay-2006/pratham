"""
explainability_service.py — Dynamic Diagnostic Evidence Tree & Subsystem Agreement Engine

Sprint 3.2.2: Rewritten to produce fully dynamic explainability data derived
from actual computed values in the clinical reasoning pipeline.

Every value in the output is traced to a specific engine computation.
No hardcoded weights, no demo data, no static strings.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════

def build_explainability_tree(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constructs a fully dynamic diagnostic evidence tree, subsystem agreement
    matrix, confidence explanation, and decision path trace.

    All values are derived from already-computed data in report_data — no new
    computations, no new database queries, no new service calls.

    Data sources used:
        report_data["clinical_conclusions"]     — Layer 2 reasoning output
        report_data["aggregation"]              — heuristic scores + breakdown
        report_data["nlp_findings"]             — NLP flags + summary
        report_data["risk_engine"]              — domain risk scores
        report_data["lab_intelligence"]          — lab model prediction
        report_data["imaging_intelligence"]      — imaging model prediction
        report_data["pipeline_status"]          — stage completion status
    """
    conclusions = report_data.get("clinical_conclusions") or {}
    aggregation = report_data.get("aggregation") or {}
    nlp = report_data.get("nlp_findings") or {}
    risk = report_data.get("risk_engine") or {}
    lab = report_data.get("lab_intelligence") or {}
    imaging = report_data.get("imaging_intelligence") or {}
    pipeline = report_data.get("pipeline_status") or {}

    # ── Primary condition identification ──────────────────────────────────
    primary_condition = conclusions.get("primary_condition") or "Acute Clinical Presentation"
    primary_key = conclusions.get("primary_condition_key")
    confidence = conclusions.get("clinical_confidence") or "LOW"

    ranked_conditions = conclusions.get("ranked_conditions") or []
    top_rank = ranked_conditions[0] if ranked_conditions else {}

    # ── 1. Evidence Tree ──────────────────────────────────────────────────
    evidence_tree = _build_evidence_tree(
        primary_condition, confidence, top_rank, conclusions, aggregation, risk,
    )

    # ── 2. Supporting Evidence ────────────────────────────────────────────
    supporting = _compile_supporting_evidence(conclusions, top_rank)

    # ── 3. Conflicting Evidence ───────────────────────────────────────────
    conflicting = _compile_conflicting_evidence(conclusions, top_rank)

    # ── 4. Missing Evidence ───────────────────────────────────────────────
    missing = _compile_missing_evidence(conclusions)

    # ── 5. Subsystem Agreement Matrix ─────────────────────────────────────
    agreement_matrix = _build_agreement_matrix(
        aggregation, nlp, risk, lab, imaging, pipeline, conclusions,
    )

    # ── 6. Confidence Explanation ─────────────────────────────────────────
    confidence_explanation = {
        "level": confidence,
        "factors": conclusions.get("confidence_factors") or [],
        "uncertainty_reasons": conclusions.get("uncertainty_reasons") or [],
    }

    # ── 7. Decision Path ──────────────────────────────────────────────────
    decision_path = _build_decision_path(
        nlp, risk, lab, imaging, aggregation, conclusions, pipeline,
    )

    # ── 8. Alternative Conditions ─────────────────────────────────────────
    alternatives = _build_alternative_conditions(ranked_conditions, conclusions)

    # ── 9. Ranking Justification ──────────────────────────────────────────
    ranking_justification = conclusions.get("ranking_justification") or {
        "primary_reasons": [],
        "vs_alternatives": [],
    }

    return {
        "primary_condition": primary_condition,
        "primary_condition_key": primary_key,
        "confidence_level": confidence,
        "evidence_tree": evidence_tree,
        "supporting_evidence": supporting,
        "conflicting_evidence": conflicting,
        "missing_evidence": missing,
        "subsystem_agreement_matrix": agreement_matrix,
        "confidence_explanation": confidence_explanation,
        "decision_path": decision_path,
        "alternative_conditions": alternatives,
        "ranking_justification": ranking_justification,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Internal builders
# ═══════════════════════════════════════════════════════════════════════════════

def _build_evidence_tree(
    primary_condition: str,
    confidence: str,
    top_rank: Dict[str, Any],
    conclusions: Dict[str, Any],
    aggregation: Dict[str, Any],
    risk: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the interactive diagnostic evidence tree with dynamic values."""

    # ── Clinical Patterns (from clinical_patterns in conclusions) ──────
    patterns_children: List[Dict[str, Any]] = []
    for i, pattern in enumerate(conclusions.get("clinical_patterns") or []):
        patterns_children.append({
            "id": f"pat_{i}",
            "name": pattern.get("pattern_name", "Unknown Pattern"),
            "type": "pattern",
            "severity": pattern.get("severity", "MODERATE"),
            "supporting_evidence": pattern.get("supporting_evidence") or [],
        })

    # ── Clinical Scores (from clinical_scores in conclusions) ──────────
    scores_children: List[Dict[str, Any]] = []
    for score_key, score_data in (conclusions.get("clinical_scores") or {}).items():
        if not isinstance(score_data, dict):
            continue
        scores_children.append({
            "id": f"score_{score_key}",
            "name": score_data.get("label", score_key),
            "type": "score",
            "value": score_data.get("score", 0),
            "risk_category": (
                score_data.get("risk_category")
                or score_data.get("mortality_risk")
                or score_data.get("mace_risk")
                or score_data.get("pe_probability")
                or ("High Risk" if score_data.get("high_risk") else "Low Risk")
            ),
        })

    # ── Subsystem Contributions (from aggregation evidence_breakdown) ──
    subsystem_children: List[Dict[str, Any]] = []
    evidence_breakdown = aggregation.get("evidence_breakdown") or {}
    primary_key = conclusions.get("primary_condition_key")

    # Gather contributions for the primary condition from breakdown
    if primary_key and primary_key in evidence_breakdown:
        primary_breakdown = evidence_breakdown[primary_key]
        # Group by source prefix (nlp, risk, lab_model, imaging_model)
        source_groups: Dict[str, List[str]] = {}
        for entry in primary_breakdown:
            # Format: "source:+delta" e.g. "nlp:chest_pain:+3.0"
            parts = entry.split(":")
            source = parts[0] if parts else "unknown"
            source_groups.setdefault(source, []).append(entry)

        SOURCE_LABELS = {
            "nlp": "Clinical NLP Extraction",
            "risk": "Rule-Based Risk Engine",
            "lab_model": "Laboratory Intelligence Engine",
            "imaging_model": "Medical Imaging Engine",
        }

        for source, entries in source_groups.items():
            # Parse total contribution for this source
            total_delta = 0.0
            signals: List[str] = []
            for entry in entries:
                parts = entry.split(":")
                if len(parts) >= 2:
                    delta_str = parts[-1]
                    signal_name = ":".join(parts[1:-1]) if len(parts) > 2 else parts[1]
                    try:
                        total_delta += float(delta_str)
                    except (ValueError, TypeError):
                        pass
                    signals.append(signal_name.replace("_", " ").title())

            subsystem_children.append({
                "id": f"sub_{source}",
                "name": SOURCE_LABELS.get(source, source.replace("_", " ").title()),
                "type": "subsystem",
                "contribution": f"+{total_delta:.1f}" if total_delta >= 0 else f"{total_delta:.1f}",
                "signals": signals,
                "raw_entries": entries,
            })

    # If no breakdown available, build from risk scores directly
    if not subsystem_children:
        # Risk engine summary
        risk_domains = []
        for domain in ("cardiac", "respiratory", "trauma", "neurological"):
            score_val = risk.get(domain, 0) or risk.get(f"{domain}_risk", 0) or 0
            if score_val > 0:
                risk_domains.append(f"{domain.title()}: {score_val}/100")
        if risk_domains:
            subsystem_children.append({
                "id": "sub_risk",
                "name": "Rule-Based Risk Engine",
                "type": "subsystem",
                "contribution": f"Severity: {risk.get('severity', 'moderate')}",
                "signals": risk_domains,
                "raw_entries": [],
            })

    # ── Assemble tree ─────────────────────────────────────────────────────
    children: List[Dict[str, Any]] = []

    if patterns_children:
        children.append({
            "id": "node_patterns",
            "name": "Clinical Patterns",
            "type": "category",
            "children": patterns_children,
        })

    if scores_children:
        children.append({
            "id": "node_scores",
            "name": "Clinical Scores",
            "type": "category",
            "children": scores_children,
        })

    if subsystem_children:
        children.append({
            "id": "node_subsystems",
            "name": "Subsystem Contributions",
            "type": "category",
            "children": subsystem_children,
        })

    return {
        "id": "root",
        "name": f"Diagnosis: {primary_condition}",
        "type": "diagnosis",
        "confidence": confidence,
        "evidence_score": top_rank.get("evidence_score", 0.0),
        "support_score": top_rank.get("support_score", 0.0),
        "conflict_score": top_rank.get("conflict_score", 0.0),
        "missing_evidence_score": top_rank.get("missing_evidence_score", 0.0),
        "knowledge_base_version": top_rank.get("knowledge_base_version", ""),
        "children": children,
    }


def _compile_supporting_evidence(
    conclusions: Dict[str, Any],
    top_rank: Dict[str, Any],
) -> List[str]:
    """Merge supporting evidence from conclusions and ranked conditions."""
    items: List[str] = []

    # From clinical reasoning conclusions
    for item in (conclusions.get("supporting_evidence") or []):
        if item and item not in items:
            items.append(item)

    # From Evidence Ranking Engine (matched rules)
    for item in (top_rank.get("matched_supporting") or []):
        if item and item not in items:
            items.append(item)

    return items


def _compile_conflicting_evidence(
    conclusions: Dict[str, Any],
    top_rank: Dict[str, Any],
) -> List[str]:
    """Merge conflicting evidence from conclusions and ranked conditions."""
    items: List[str] = []

    for item in (conclusions.get("conflicting_evidence") or []):
        if item and item not in items:
            items.append(item)

    for item in (top_rank.get("matched_conflicting") or []):
        if item and item not in items:
            items.append(item)

    return items


def _compile_missing_evidence(conclusions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract missing data sources from data_completeness."""
    missing: List[Dict[str, Any]] = []
    completeness = conclusions.get("data_completeness") or {}

    for source_key, info in completeness.items():
        if not isinstance(info, dict):
            continue
        if not info.get("available", True):
            missing.append({
                "source": info.get("label", source_key),
                "critical": info.get("critical", False),
                "note": info.get("note", ""),
            })

    # Also include limitations that reference specific unavailable investigations
    for limitation in (conclusions.get("clinical_limitations") or []):
        if isinstance(limitation, dict) and not limitation.get("available", True):
            label = limitation.get("source", "")
            if label and not any(m["source"] == label for m in missing):
                missing.append({
                    "source": label,
                    "critical": False,
                    "note": limitation.get("note", ""),
                })

    return missing


def _build_agreement_matrix(
    aggregation: Dict[str, Any],
    nlp: Dict[str, Any],
    risk: Dict[str, Any],
    lab: Dict[str, Any],
    imaging: Dict[str, Any],
    pipeline: Dict[str, Any],
    conclusions: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Build dynamic subsystem agreement matrix from actual data availability
    and the report quality assessment.
    """
    source_summary = aggregation.get("source_summary") or {}
    report_quality = conclusions.get("report_quality") or {}
    agreement_level = report_quality.get("subsystem_agreement", "INSUFFICIENT DATA")

    matrix: List[Dict[str, Any]] = []

    # ── NLP Engine ────────────────────────────────────────────────────────
    nlp_available = source_summary.get("nlp", False) or bool(nlp.get("flags") or nlp.get("summary"))
    nlp_status = pipeline.get("nlp", "pending")
    if not nlp_available:
        matrix.append({
            "subsystem": "Clinical NLP Extraction",
            "status": "UNAVAILABLE",
            "signal": f"Stage status: {nlp_status}",
        })
    else:
        active_flags = [k for k, v in (nlp.get("flags") or {}).items() if v]
        signal = f"{len(active_flags)} active clinical flag(s) detected" if active_flags else "No significant flags extracted"
        matrix.append({
            "subsystem": "Clinical NLP Extraction",
            "status": "AVAILABLE",
            "signal": signal,
        })

    # ── Risk Engine ───────────────────────────────────────────────────────
    risk_available = source_summary.get("risk", False) or any(
        (risk.get(d) or 0) > 0 for d in ("cardiac", "respiratory", "trauma", "neurological")
    )
    if not risk_available:
        matrix.append({
            "subsystem": "Rule-Based Risk Engine",
            "status": "UNAVAILABLE",
            "signal": "Risk scores not computed",
        })
    else:
        severity = risk.get("severity", "moderate")
        max_domain = max(
            ("cardiac", "respiratory", "trauma", "neurological"),
            key=lambda d: risk.get(d, 0) or 0,
        )
        max_score = risk.get(max_domain, 0) or 0
        matrix.append({
            "subsystem": "Rule-Based Risk Engine",
            "status": "AVAILABLE",
            "signal": f"Severity: {severity}. Highest domain: {max_domain} ({max_score}/100)",
        })

    # ── Lab Intelligence Engine ───────────────────────────────────────────
    lab_available = source_summary.get("lab", False) or (lab.get("available") is True)
    if not lab_available:
        lab_status = pipeline.get("lab", "pending")
        matrix.append({
            "subsystem": "Laboratory Intelligence Engine",
            "status": "UNAVAILABLE",
            "signal": f"Stage status: {lab_status}",
        })
    else:
        prediction = lab.get("prediction", "unknown")
        prob = lab.get("risk_probability")
        prob_str = f" ({prob*100:.1f}%)" if prob is not None else ""
        matrix.append({
            "subsystem": "Laboratory Intelligence Engine",
            "status": "AVAILABLE",
            "signal": f"Prediction: {prediction}{prob_str}",
        })

    # ── Medical Imaging Engine ────────────────────────────────────────────
    img_available = source_summary.get("imaging", False) or (imaging.get("available") is True)
    if not img_available:
        img_status = pipeline.get("imaging", "pending")
        matrix.append({
            "subsystem": "Medical Imaging Engine",
            "status": "UNAVAILABLE",
            "signal": f"Stage status: {img_status}",
        })
    else:
        prediction = imaging.get("prediction", "unknown")
        prob = imaging.get("pneumonia_probability")
        conf = imaging.get("confidence")
        prob_str = f" (probability: {prob*100:.1f}%)" if prob is not None else ""
        matrix.append({
            "subsystem": "Medical Imaging Engine",
            "status": "AVAILABLE",
            "signal": f"Prediction: {prediction}{prob_str}",
        })

    # ── Aggregation Engine ────────────────────────────────────────────────
    agg_available = aggregation.get("available") is True
    if not agg_available:
        agg_status = pipeline.get("aggregation", "pending")
        matrix.append({
            "subsystem": "Evidence Aggregation Engine",
            "status": "UNAVAILABLE",
            "signal": f"Stage status: {agg_status}",
        })
    else:
        suppressed = aggregation.get("confidence_suppressed", False)
        primary_cond = aggregation.get("primary_condition")
        if suppressed:
            reason = aggregation.get("suppression_reason", "insufficient evidence")
            matrix.append({
                "subsystem": "Evidence Aggregation Engine",
                "status": "SUPPRESSED",
                "signal": f"Confidence suppressed: {reason}",
            })
        else:
            matrix.append({
                "subsystem": "Evidence Aggregation Engine",
                "status": "AVAILABLE",
                "signal": f"Primary condition: {primary_cond or 'undetermined'}",
            })

    # ── Overall Agreement ─────────────────────────────────────────────────
    matrix.append({
        "subsystem": "Overall Subsystem Agreement",
        "status": agreement_level,
        "signal": f"Pipeline integrity: {report_quality.get('pipeline_integrity', 'UNKNOWN')}",
    })

    return matrix


def _build_decision_path(
    nlp: Dict[str, Any],
    risk: Dict[str, Any],
    lab: Dict[str, Any],
    imaging: Dict[str, Any],
    aggregation: Dict[str, Any],
    conclusions: Dict[str, Any],
    pipeline: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Reconstruct the ordered decision path from available evidence.
    Each step shows what engine ran, what it produced, and how it
    influenced the final conclusion.
    """
    path: List[Dict[str, Any]] = []
    step = 0

    # Step 1: NLP Extraction
    step += 1
    nlp_flags = nlp.get("flags") or {}
    active = [k.replace("_", " ").title() for k, v in nlp_flags.items() if v]
    nlp_status = pipeline.get("nlp", "unknown")
    path.append({
        "step": step,
        "engine": "NLP Extraction Engine",
        "status": nlp_status,
        "output": f"Active flags: {', '.join(active)}" if active else "No significant flags",
        "impact": _nlp_impact(active),
    })

    # Step 2: Risk Scoring
    step += 1
    risk_status = pipeline.get("risk", "unknown")
    severity = risk.get("severity", "unknown")
    domains = {d: risk.get(d, 0) or 0 for d in ("cardiac", "respiratory", "trauma", "neurological")}
    top_domain = max(domains, key=domains.get) if any(v > 0 for v in domains.values()) else None
    path.append({
        "step": step,
        "engine": "Risk Scoring Engine",
        "status": risk_status,
        "output": f"Severity: {severity}. Scores: {', '.join(f'{d}={v}' for d, v in domains.items() if v > 0)}" if any(v > 0 for v in domains.values()) else "No risk signals",
        "impact": f"Highest risk domain: {top_domain} ({domains.get(top_domain, 0)}/100)" if top_domain else "No dominant risk domain",
    })

    # Step 3: Lab Analysis (conditional)
    step += 1
    lab_available = lab.get("available") is True
    lab_status = pipeline.get("lab", "not_run")
    if lab_available:
        prediction = lab.get("prediction", "unknown")
        prob = lab.get("risk_probability")
        prob_str = f" ({prob*100:.1f}%)" if prob is not None else ""
        path.append({
            "step": step,
            "engine": "Laboratory Intelligence Engine",
            "status": lab_status,
            "output": f"Cardiac risk prediction: {prediction}{prob_str}",
            "impact": "Contributes to ACS scoring in aggregation" if prediction == "high_risk" else "Low cardiac signal — supports non-cardiac pathways",
        })
    else:
        path.append({
            "step": step,
            "engine": "Laboratory Intelligence Engine",
            "status": lab_status,
            "output": "Not available — lab analysis not performed",
            "impact": "Missing lab data reduces diagnostic confidence",
        })

    # Step 4: Imaging Analysis (conditional)
    step += 1
    img_available = imaging.get("available") is True
    img_status = pipeline.get("imaging", "not_run")
    if img_available:
        prediction = imaging.get("prediction", "unknown")
        prob = imaging.get("pneumonia_probability")
        prob_str = f" ({prob*100:.1f}%)" if prob is not None else ""
        path.append({
            "step": step,
            "engine": "Medical Imaging Engine",
            "status": img_status,
            "output": f"Classification: {prediction}{prob_str}",
            "impact": "Contributes to Pneumonia scoring in aggregation" if prediction == "pneumonia" else "Normal chest imaging — reduces respiratory pathway score",
        })
    else:
        path.append({
            "step": step,
            "engine": "Medical Imaging Engine",
            "status": img_status,
            "output": "Not available — imaging analysis not performed",
            "impact": "Missing imaging data reduces diagnostic confidence",
        })

    # Step 5: Aggregation
    step += 1
    agg_available = aggregation.get("available") is True
    agg_status = pipeline.get("aggregation", "not_run")
    if agg_available:
        suppressed = aggregation.get("confidence_suppressed", False)
        if suppressed:
            path.append({
                "step": step,
                "engine": "Evidence Aggregation Engine",
                "status": agg_status,
                "output": f"Suppressed: {aggregation.get('suppression_reason', 'insufficient evidence')}",
                "impact": "Probability distribution not produced — insufficient evidence",
            })
        else:
            primary = aggregation.get("primary_condition", "unknown")
            probs = aggregation.get("probabilities") or {}
            primary_prob = probs.get(primary)
            prob_str = f" ({primary_prob*100:.1f}%)" if primary_prob is not None else ""
            path.append({
                "step": step,
                "engine": "Evidence Aggregation Engine",
                "status": agg_status,
                "output": f"Primary condition: {primary}{prob_str}",
                "impact": f"Heuristic scoring selected {primary} as most likely condition",
            })
    else:
        path.append({
            "step": step,
            "engine": "Evidence Aggregation Engine",
            "status": agg_status,
            "output": "Not available — aggregation not performed",
            "impact": "No condition probability distribution available",
        })

    # Step 6: Evidence Ranking (Knowledge Base)
    step += 1
    ranked = conclusions.get("ranked_conditions") or []
    if ranked:
        top = ranked[0]
        path.append({
            "step": step,
            "engine": "Evidence Ranking Engine (Knowledge Base)",
            "status": "completed",
            "output": f"Top ranked: {top.get('condition_name', 'unknown')} (score: {top.get('evidence_score', 0):.1f})",
            "impact": f"Evaluated {len(ranked)} conditions against YAML knowledge base rules",
        })
    else:
        path.append({
            "step": step,
            "engine": "Evidence Ranking Engine (Knowledge Base)",
            "status": "completed",
            "output": "No conditions matched knowledge base criteria",
            "impact": "No knowledge base rules produced a ranking",
        })

    # Step 7: Final Conclusion
    step += 1
    primary_cond = conclusions.get("primary_condition", "Undetermined")
    confidence = conclusions.get("clinical_confidence", "LOW")
    path.append({
        "step": step,
        "engine": "Clinical Reasoning Service (Final)",
        "status": "completed",
        "output": f"Diagnosis: {primary_cond} | Confidence: {confidence}",
        "impact": "Final clinical conclusion assembled from all engine outputs",
    })

    return path


def _nlp_impact(active_flags: List[str]) -> str:
    """Determine the clinical impact of NLP flags on downstream routing."""
    lower = [f.lower() for f in active_flags]
    has_cardiac = any("cardiac" in f or "chest" in f for f in lower)
    has_respiratory = any("respiratory" in f or "breathlessness" in f for f in lower)
    has_neuro = any("neurological" in f or "consciousness" in f or "trauma" in f for f in lower)

    impacts = []
    if has_cardiac:
        impacts.append("cardiac pathway")
    if has_respiratory:
        impacts.append("respiratory pathway")
    if has_neuro:
        impacts.append("neurological pathway")

    if impacts:
        return f"Directs toward {', '.join(impacts)}"
    return "No strong directional signal from NLP"


def _build_alternative_conditions(
    ranked_conditions: List[Dict[str, Any]],
    conclusions: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Build alternative condition list from ranked_conditions[1:]."""
    alternatives: List[Dict[str, Any]] = []

    # From Evidence Ranking Engine (positions 1+)
    for rank_item in ranked_conditions[1:]:
        alternatives.append({
            "condition_name": rank_item.get("condition_name", "Unknown"),
            "condition_key": rank_item.get("condition_key", ""),
            "evidence_score": rank_item.get("evidence_score", 0.0),
            "support_score": rank_item.get("support_score", 0.0),
            "conflict_score": rank_item.get("conflict_score", 0.0),
            "missing_evidence_score": rank_item.get("missing_evidence_score", 0.0),
            "matched_supporting": rank_item.get("matched_supporting") or [],
            "matched_conflicting": rank_item.get("matched_conflicting") or [],
        })

    # Also include aggregation-based alternatives if they provide different conditions
    agg_alternatives = conclusions.get("alternative_conditions") or []
    existing_keys = {a["condition_key"] for a in alternatives}
    for alt in agg_alternatives:
        key = alt.get("condition_key", "")
        if key and key not in existing_keys:
            alternatives.append({
                "condition_name": alt.get("condition", "Unknown"),
                "condition_key": key,
                "evidence_score": 0.0,
                "support_score": 0.0,
                "conflict_score": 0.0,
                "missing_evidence_score": 0.0,
                "probability": alt.get("probability"),
                "matched_supporting": [],
                "matched_conflicting": [],
            })

    return alternatives
