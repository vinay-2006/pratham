"""Architecture Validation Script — M6.5"""
import ast, os, sys

# 1. Check shared layer has no domain imports
shared_path = os.path.join("app", "domains", "shared")
violations = []
for root, dirs, files in os.walk(shared_path):
    for f in files:
        if not f.endswith(".py"):
            continue
        fpath = os.path.join(root, f)
        with open(fpath, "r", encoding="utf-8") as fp:
            tree = ast.parse(fp.read(), filename=fpath)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
                if mod.startswith("app.domains.") and not mod.startswith("app.domains.shared"):
                    violations.append(f"shared/{f} imports {mod}")

if violations:
    print("SHARED LAYER VIOLATIONS:")
    for v in violations:
        print(f"  {v}")
else:
    print("[OK] shared/ imports no domain modules")

# 2. Check cross-domain imports
DOMAINS_ROOT = os.path.join("app", "domains")
domain_files = {}
for domain in os.listdir(DOMAINS_ROOT):
    domain_path = os.path.join(DOMAINS_ROOT, domain)
    if not os.path.isdir(domain_path):
        continue
    for root, dirs, files in os.walk(domain_path):
        for f in files:
            if f.endswith(".py"):
                fpath = os.path.join(root, f)
                domain_files.setdefault(domain, []).append(fpath)

cross_violations = []
for domain, files in domain_files.items():
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as fp:
                tree = ast.parse(fp.read(), filename=fpath)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
                if mod.startswith("app.domains."):
                    parts = mod.split(".")
                    if len(parts) >= 3:
                        target = parts[2]
                        if target != domain and target != "shared":
                            cross_violations.append(f"{domain}/{os.path.basename(fpath)} -> {target}")

if cross_violations:
    print("CROSS-DOMAIN VIOLATIONS:")
    for v in cross_violations:
        print(f"  {v}")
else:
    total = sum(len(v) for v in domain_files.values())
    print(f"[OK] No cross-domain imports ({total} files, {len(domain_files)} domains)")

# 3. Protocol compliance
from app.domains.shared.interfaces import (
    PatientRepositoryProtocol, IntakeRepositoryProtocol, VitalsRepositoryProtocol,
    SymptomsRepositoryProtocol, WorkflowRepositoryProtocol, InvestigationRepositoryProtocol,
    EvidenceRepositoryProtocol, PipelineRepositoryProtocol, AlertsRepositoryProtocol,
    NLPRepositoryProtocol, RiskScoresRepositoryProtocol,
)
from app.domains.patient.repository import PatientRepository
from app.domains.triage.repository import IntakeRepository, VitalsRepository, SymptomsRepository
from app.domains.workflow.repository import WorkflowRepository
from app.domains.investigation.repository import InvestigationRepository
from app.domains.evidence.repository import EvidenceRepository
from app.domains.pipeline.repository import PipelineRepository
from app.domains.notification.repository import AlertsRepository
from app.domains.ai.repository import NLPRepository, RiskScoresRepository

checks = [
    ("PatientRepository", PatientRepository(), PatientRepositoryProtocol),
    ("IntakeRepository", IntakeRepository(), IntakeRepositoryProtocol),
    ("VitalsRepository", VitalsRepository(), VitalsRepositoryProtocol),
    ("SymptomsRepository", SymptomsRepository(), SymptomsRepositoryProtocol),
    ("WorkflowRepository", WorkflowRepository(), WorkflowRepositoryProtocol),
    ("InvestigationRepository", InvestigationRepository(), InvestigationRepositoryProtocol),
    ("EvidenceRepository", EvidenceRepository(), EvidenceRepositoryProtocol),
    ("PipelineRepository", PipelineRepository(), PipelineRepositoryProtocol),
    ("AlertsRepository", AlertsRepository(), AlertsRepositoryProtocol),
    ("NLPRepository", NLPRepository(), NLPRepositoryProtocol),
    ("RiskScoresRepository", RiskScoresRepository(), RiskScoresRepositoryProtocol),
]

print("\nPROTOCOL COMPLIANCE:")
all_pass = True
for name, inst, proto in checks:
    ok = isinstance(inst, proto)
    status = "PASS" if ok else "FAIL"
    print(f"  {name}: {status}")
    if not ok:
        all_pass = False

# 4. Verify existing code still works
from app.api import intake, investigations, evidence, report, pipeline
print("\n[OK] All existing API modules still importable")

print("\n=== ARCHITECTURE VALIDATION COMPLETE ===")
if violations or cross_violations or not all_pass:
    sys.exit(1)
