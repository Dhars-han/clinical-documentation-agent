import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set

try:
    from backend.validation.schemas import ValidationIssue, ValidationResult
    from backend.validation.rules import RULES
    from backend.documentation.schemas import ClinicalFollowUpRecord
    from backend.evidence_agent import EvidencePackage
    from backend.reconciliation.schemas import ReconciliationReport, ReconciliationStatus
except ImportError:
    from .schemas import ValidationIssue, ValidationResult
    from .rules import RULES
    from ..documentation.schemas import ClinicalFollowUpRecord
    from ..evidence_agent import EvidencePackage
    from ..reconciliation.schemas import ReconciliationReport, ReconciliationStatus


class ClinicalValidator:
    """Deterministic, rule-based verification agent for ClinicalFollowUpRecords.
    
    Verifies:
    1. Schema integrity (RULE-001..003)
    2. Evidence grounding (RULE-001..003)
    3. Hallucination / unsupported claim detection (RULE-008)
    4. Reconciliation consistency (RULE-004)
    5. Conflict preservation (RULE-005)
    6. Allergy safety validation (RULE-006)
    7. Clinical RAG separation (RULE-007)
    8. Uncertainty and ambiguity handling (RULE-009)
    9. Follow-up action safety boundaries (RULE-010)
    """

    CHECKS = [
        "schema_validation",
        "evidence_grounding",
        "hallucination_detection",
        "reconciliation_consistency",
        "conflict_preservation",
        "allergy_safety",
        "rag_separation",
        "uncertainty_handling",
        "safety_boundary"
    ]

    @classmethod
    def validate(
        cls,
        record: ClinicalFollowUpRecord,
        evidence_package: Optional[EvidencePackage] = None,
        reconciliation_report: Optional[ReconciliationReport] = None,
        rag_contexts: Optional[List[Dict[str, Any]]] = None
    ) -> ValidationResult:
        """Executes deterministic validation checks and produces an explainable verdict."""
        issues: List[ValidationIssue] = []

        # 1. Schema Validation
        cls._check_schema(record, issues)

        # 2. Evidence Grounding (RULE-001, RULE-002, RULE-003)
        cls._check_evidence_grounding(record, issues)

        # 3. Hallucination / Unsupported Claims (RULE-008)
        if evidence_package:
            cls._check_hallucinations(record, evidence_package, issues)

        # 4. Reconciliation Consistency (RULE-004)
        if reconciliation_report:
            cls._check_reconciliation_consistency(record, reconciliation_report, issues)

        # 5. Conflict Preservation (RULE-005)
        if reconciliation_report:
            cls._check_conflict_preservation(record, reconciliation_report, issues)

        # 6. Allergy Safety (RULE-006)
        cls._check_allergy_safety(record, reconciliation_report, evidence_package, issues)

        # 7. RAG Separation (RULE-007)
        cls._check_rag_separation(record, issues)

        # 8. Uncertainty Handling (RULE-009)
        if reconciliation_report:
            cls._check_uncertainty_handling(record, reconciliation_report, issues)

        # 9. Follow-up Action Safety Boundary (RULE-010)
        cls._check_safety_boundary(record, issues)

        # Compute Category Passes
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]

        evidence_grounding_passed = not any(
            i.category in ("evidence_grounding", "hallucination") and i.severity == "error"
            for i in issues
        )
        reconciliation_consistency_passed = not any(
            i.category == "reconciliation_consistency" and i.severity == "error"
            for i in issues
        )
        conflict_preservation_passed = not any(
            i.category in ("conflict_preservation", "allergy_safety") and i.severity == "error"
            for i in issues
        )
        rag_separation_passed = not any(
            i.category == "rag_separation" and i.severity == "error"
            for i in issues
        )
        uncertainty_handling_passed = not any(
            i.category == "uncertainty_handling" and i.severity == "error"
            for i in issues
        )
        safety_boundary_passed = not any(
            i.category == "safety_boundary" and i.severity == "error"
            for i in issues
        )

        passed = len(errors) == 0

        # Overall requires_human_review is True if the underlying clinical record escalated it,
        # or if any validation issue requires human escalation
        escalation_required = (
            record.requires_human_review or
            any(i.category in ("safety_boundary", "conflict_preservation", "allergy_safety") for i in issues)
        )

        # Set validation_status
        if not passed:
            validation_status = "failed"
        elif len(warnings) > 0:
            validation_status = "requires_human_review"
        else:
            validation_status = "passed"

        return ValidationResult(
            patient_id=record.patient_id,
            validation_status=validation_status,
            passed=passed,
            issues=issues,
            checks_performed=cls.CHECKS,
            evidence_grounding_passed=evidence_grounding_passed,
            reconciliation_consistency_passed=reconciliation_consistency_passed,
            conflict_preservation_passed=conflict_preservation_passed,
            rag_separation_passed=rag_separation_passed,
            uncertainty_handling_passed=uncertainty_handling_passed,
            safety_boundary_passed=safety_boundary_passed,
            requires_human_review=escalation_required,
            validated_at=datetime.now(timezone.utc).isoformat()
        )

    # -------------------------------------------------------------------------
    # 1. Schema Validation
    # -------------------------------------------------------------------------
    @classmethod
    def _check_schema(cls, record: ClinicalFollowUpRecord, issues: List[ValidationIssue]):
        if not record.patient_id or not str(record.patient_id).strip():
            issues.append(ValidationIssue(
                category="schema",
                severity="error",
                message="ClinicalFollowUpRecord missing required non-empty 'patient_id'.",
                rule_id="RULE-001"
            ))

        if not hasattr(record, "consultation_summary") or record.consultation_summary is None:
            issues.append(ValidationIssue(
                category="schema",
                severity="error",
                message="ClinicalFollowUpRecord missing 'consultation_summary'.",
                rule_id="RULE-001"
            ))

        required_lists = [
            ("medications", record.medications),
            ("allergies", record.allergies),
            ("relevant_labs", record.relevant_labs),
            ("documented_changes", record.documented_changes),
            ("unresolved_conflicts", record.unresolved_conflicts),
            ("follow_up_actions", record.follow_up_actions),
            ("clinical_references", record.clinical_references),
        ]

        for field_name, val in required_lists:
            if val is None or not isinstance(val, list):
                issues.append(ValidationIssue(
                    category="schema",
                    severity="error",
                    message=f"ClinicalFollowUpRecord field '{field_name}' must be a valid list.",
                    rule_id="RULE-001"
                ))

        if len(record.unresolved_conflicts) != record.unresolved_conflict_count:
            issues.append(ValidationIssue(
                category="schema",
                severity="warning",
                message=f"Unresolved conflict count mismatch: count is {record.unresolved_conflict_count}, but list has {len(record.unresolved_conflicts)} items.",
                rule_id="RULE-005"
            ))

    # -------------------------------------------------------------------------
    # 2. Evidence Grounding (RULE-001, RULE-002, RULE-003)
    # -------------------------------------------------------------------------
    @classmethod
    def _check_evidence_grounding(cls, record: ClinicalFollowUpRecord, issues: List[ValidationIssue]):
        # Check medications (RULE-001)
        for med in record.medications:
            if not med.evidence_references or len(med.evidence_references) == 0:
                issues.append(ValidationIssue(
                    category="evidence_grounding",
                    severity="error",
                    rule_id="RULE-001",
                    entity=med.name,
                    message=f"Documented medication '{med.name}' lacks supporting evidence references."
                ))
            else:
                for ev in med.evidence_references:
                    if not ev.source or not ev.raw_excerpt:
                        issues.append(ValidationIssue(
                            category="evidence_grounding",
                            severity="error",
                            rule_id="RULE-001",
                            entity=med.name,
                            message=f"Evidence reference for medication '{med.name}' is missing source or raw excerpt."
                        ))

        # Check allergies (RULE-002)
        for allergy in record.allergies:
            if not allergy.evidence_references or len(allergy.evidence_references) == 0:
                issues.append(ValidationIssue(
                    category="evidence_grounding",
                    severity="error",
                    rule_id="RULE-002",
                    entity=allergy.allergen,
                    message=f"Documented allergy '{allergy.allergen}' lacks supporting evidence references."
                ))
            else:
                for ev in allergy.evidence_references:
                    if not ev.source or not ev.raw_excerpt:
                        issues.append(ValidationIssue(
                            category="evidence_grounding",
                            severity="error",
                            rule_id="RULE-002",
                            entity=allergy.allergen,
                            message=f"Evidence reference for allergy '{allergy.allergen}' is missing source or raw excerpt."
                        ))

        # Check laboratory measurements (RULE-003)
        for lab in record.relevant_labs:
            if not lab.evidence_references or len(lab.evidence_references) == 0:
                issues.append(ValidationIssue(
                    category="evidence_grounding",
                    severity="error",
                    rule_id="RULE-003",
                    entity=lab.test_name,
                    message=f"Documented laboratory test '{lab.test_name}' lacks supporting evidence references."
                ))
            else:
                for ev in lab.evidence_references:
                    if not ev.source or not ev.raw_excerpt:
                        issues.append(ValidationIssue(
                            category="evidence_grounding",
                            severity="error",
                            rule_id="RULE-003",
                            entity=lab.test_name,
                            message=f"Evidence reference for lab '{lab.test_name}' is missing source or raw excerpt."
                        ))

        # Check documented changes
        for chg in record.documented_changes:
            if not chg.evidence_references or len(chg.evidence_references) == 0:
                issues.append(ValidationIssue(
                    category="evidence_grounding",
                    severity="error",
                    rule_id="RULE-001",
                    entity=chg.entity,
                    message=f"Documented change for '{chg.entity}' lacks supporting evidence references."
                ))

    # -------------------------------------------------------------------------
    # 3. Hallucination / Unsupported Claim Detection (RULE-008)
    # -------------------------------------------------------------------------
    @classmethod
    def _check_hallucinations(
        cls,
        record: ClinicalFollowUpRecord,
        evidence_package: EvidencePackage,
        issues: List[ValidationIssue]
    ):
        # Index evidence entities and texts
        known_med_entities = {
            it.entity_name.lower().strip() for it in evidence_package.items
            if it.category.value == "medication"
        }
        known_allergy_entities = {
            it.entity_name.lower().strip() for it in evidence_package.items
            if it.category.value == "allergy"
        }
        known_lab_entities = {
            it.entity_name.lower().strip() for it in evidence_package.items
            if it.category.value == "lab"
        }

        all_evidence_text = " ".join([it.raw_text for it in evidence_package.items]).lower()

        # Check for ungrounded medications
        for med in record.medications:
            med_name_clean = med.name.lower().strip()
            if med_name_clean not in known_med_entities and med_name_clean not in all_evidence_text:
                issues.append(ValidationIssue(
                    category="hallucination",
                    severity="error",
                    rule_id="RULE-008",
                    entity=med.name,
                    message=f"Documented medication '{med.name}' does not exist in patient evidence package."
                ))
                continue

            # Check for hallucinated / unsupported dosage or regimen
            if med.regimen and med.regimen.lower() not in ("discontinued", "unknown", "none"):
                # Extract numeric dosage values like "1000 mg", "500 mg", "10 mg", "20 mg"
                documented_numbers = re.findall(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units)\b", med.regimen.lower())
                for d_num in documented_numbers:
                    # Check if this dosage exists in evidence for this medication
                    num_found = False
                    for it in evidence_package.items:
                        if it.category.value == "medication" and it.entity_name.lower() == med_name_clean:
                            if d_num in it.raw_text.lower() or d_num in str(it.attributes).lower():
                                num_found = True
                                break
                    if not num_found:
                        issues.append(ValidationIssue(
                            category="hallucination",
                            severity="error",
                            rule_id="RULE-008",
                            entity=med.name,
                            message=f"Documented regimen '{med.regimen}' contains dosage '{d_num}' unsupported by evidence for '{med.name}'."
                        ))

        # Check for ungrounded allergies
        for allergy in record.allergies:
            allergen_clean = allergy.allergen.lower().strip()
            if allergen_clean in ("no known allergies", "no known drug allergies", "none"):
                continue
            if allergen_clean not in known_allergy_entities and allergen_clean not in all_evidence_text:
                issues.append(ValidationIssue(
                    category="hallucination",
                    severity="error",
                    rule_id="RULE-008",
                    entity=allergy.allergen,
                    message=f"Documented allergy allergen '{allergy.allergen}' is absent from patient evidence sources."
                ))

        # Check for ungrounded labs
        for lab in record.relevant_labs:
            lab_clean = lab.test_name.lower().strip()
            if lab_clean not in known_lab_entities and lab_clean not in all_evidence_text:
                issues.append(ValidationIssue(
                    category="hallucination",
                    severity="error",
                    rule_id="RULE-008",
                    entity=lab.test_name,
                    message=f"Documented laboratory test '{lab.test_name}' is absent from evidence records."
                ))
            else:
                # Check value grounding
                matching_lab_items = [
                    it for it in evidence_package.items
                    if it.category.value == "lab" and (it.entity_name.lower() == lab_clean or lab_clean in it.raw_text.lower())
                ]
                value_found = False
                val_clean = lab.value.strip().lower()
                for it in matching_lab_items:
                    ev_val = str(it.attributes.get("value", "")).strip().lower()
                    if val_clean == ev_val or val_clean in it.raw_text.lower():
                        value_found = True
                        break
                if matching_lab_items and not value_found:
                    issues.append(ValidationIssue(
                        category="hallucination",
                        severity="error",
                        rule_id="RULE-008",
                        entity=lab.test_name,
                        message=f"Documented lab value '{lab.value}' for '{lab.test_name}' cannot be found in underlying evidence."
                    ))

    # -------------------------------------------------------------------------
    # 4. Reconciliation Consistency (RULE-004)
    # -------------------------------------------------------------------------
    @classmethod
    def _check_reconciliation_consistency(
        cls,
        record: ClinicalFollowUpRecord,
        reconciliation_report: ReconciliationReport,
        issues: List[ValidationIssue]
    ):
        recon_map = {r.entity.lower().strip(): r for r in reconciliation_report.results}

        for med in record.medications:
            r = recon_map.get(med.name.lower().strip())
            if not r:
                continue

            # Check Discontinuation consistency
            if r.status == ReconciliationStatus.RESOLVED and "discontinued" in (r.current_state or "").lower():
                if med.status.lower() == "active":
                    issues.append(ValidationIssue(
                        category="reconciliation_consistency",
                        severity="error",
                        rule_id="RULE-004",
                        entity=med.name,
                        message=f"Medication '{med.name}' documented as 'active', but Phase 3 reconciliation resolved it as 'discontinued'."
                    ))

            # Check Active consistency
            elif r.status == ReconciliationStatus.CONSISTENT and "active" in (r.current_state or "").lower():
                if med.status.lower() == "discontinued":
                    issues.append(ValidationIssue(
                        category="reconciliation_consistency",
                        severity="error",
                        rule_id="RULE-004",
                        entity=med.name,
                        message=f"Medication '{med.name}' documented as 'discontinued', but Phase 3 reconciliation established it is 'active'."
                    ))

            # Check Conflict consistency
            elif r.status == ReconciliationStatus.CONFLICT:
                if med.status.lower() not in ("conflicting", "conflict", "unresolved"):
                    issues.append(ValidationIssue(
                        category="reconciliation_consistency",
                        severity="error",
                        rule_id="RULE-004",
                        entity=med.name,
                        message=f"Medication '{med.name}' documented with definite status '{med.status}', contradicting Phase 3 unresolved conflict verdict."
                    ))
                if not med.requires_human_review:
                    issues.append(ValidationIssue(
                        category="reconciliation_consistency",
                        severity="error",
                        rule_id="RULE-004",
                        entity=med.name,
                        message=f"Medication '{med.name}' has reconciliation conflict but requires_human_review is False."
                    ))

    # -------------------------------------------------------------------------
    # 5. Conflict Preservation (RULE-005)
    # -------------------------------------------------------------------------
    @classmethod
    def _check_conflict_preservation(
        cls,
        record: ClinicalFollowUpRecord,
        reconciliation_report: ReconciliationReport,
        issues: List[ValidationIssue]
    ):
        unresolved_entities = [
            r for r in reconciliation_report.results
            if r.status in (ReconciliationStatus.CONFLICT, ReconciliationStatus.UNRESOLVED)
        ]

        for u in unresolved_entities:
            # 1. Human review must be triggered
            if not record.requires_human_review:
                issues.append(ValidationIssue(
                    category="conflict_preservation",
                    severity="error",
                    rule_id="RULE-005",
                    entity=u.entity,
                    message=f"Reconciliation identified conflict in '{u.entity}', but record requires_human_review is False."
                ))

            # 2. Must be listed in unresolved_conflicts
            entity_name_clean = u.entity.lower().strip()
            preserved = any(entity_name_clean in c.lower() for c in record.unresolved_conflicts)
            if not preserved:
                issues.append(ValidationIssue(
                    category="conflict_preservation",
                    severity="error",
                    rule_id="RULE-005",
                    entity=u.entity,
                    message=f"Reconciliation conflict for '{u.entity}' was not preserved in documentation unresolved_conflicts."
                ))

    # -------------------------------------------------------------------------
    # 6. Allergy Safety Validation (RULE-006)
    # -------------------------------------------------------------------------
    @classmethod
    def _check_allergy_safety(
        cls,
        record: ClinicalFollowUpRecord,
        reconciliation_report: Optional[ReconciliationReport],
        evidence_package: Optional[EvidencePackage],
        issues: List[ValidationIssue]
    ):
        if not reconciliation_report:
            return

        for r in reconciliation_report.results:
            if r.category == "allergy" and r.status == ReconciliationStatus.CONFLICT:
                # Find matching allergy in documentation
                matching_allergies = [
                    a for a in record.allergies
                    if a.allergen.lower().strip() == r.entity.lower().strip()
                ]

                # Check if documentation erased the allergy
                if not matching_allergies:
                    # Check if documentation simply claims "no known allergies"
                    denial_only = any(
                        a.status.lower() in ("no_known_allergies", "none") or
                        "no known" in (a.reported_statement or "").lower()
                        for a in record.allergies
                    )
                    if denial_only:
                        issues.append(ValidationIssue(
                            category="allergy_safety",
                            severity="error",
                            rule_id="RULE-006",
                            entity=r.entity,
                            message=f"Allergy conflict for '{r.entity}' was erased. Documentation states 'no known allergies' despite medical database record."
                        ))
                    else:
                        issues.append(ValidationIssue(
                            category="allergy_safety",
                            severity="error",
                            rule_id="RULE-006",
                            entity=r.entity,
                            message=f"Allergy conflict for '{r.entity}' was omitted from documented allergies."
                        ))
                    continue

                for doc_a in matching_allergies:
                    if doc_a.status.lower() == "no_known_allergies":
                        issues.append(ValidationIssue(
                            category="allergy_safety",
                            severity="error",
                            rule_id="RULE-006",
                            entity=doc_a.allergen,
                            message=f"Allergy '{doc_a.allergen}' documented as 'no_known_allergies' despite database evidence. Allergy profile must NOT be deleted without clinical review."
                        ))
                    if not doc_a.requires_human_review:
                        issues.append(ValidationIssue(
                            category="allergy_safety",
                            severity="error",
                            rule_id="RULE-006",
                            entity=doc_a.allergen,
                            message=f"Conflicting allergy '{doc_a.allergen}' must have requires_human_review=True."
                        ))
                    if doc_a.status.lower() != "conflicting":
                        issues.append(ValidationIssue(
                            category="allergy_safety",
                            severity="error",
                            rule_id="RULE-006",
                            entity=doc_a.allergen,
                            message=f"Conflicting allergy '{doc_a.allergen}' must have status='conflicting'."
                        ))

    # -------------------------------------------------------------------------
    # 7. Clinical RAG Separation Validation (RULE-007)
    # -------------------------------------------------------------------------
    @classmethod
    def _check_rag_separation(cls, record: ClinicalFollowUpRecord, issues: List[ValidationIssue]):
        forbidden_source_keywords = [
            "guideline", "clinical_guideline", "rag", "reference_document",
            "doc-ada", "doc-endo", "doc-kdigo", "doc-aaaai", "doc-deprescribing"
        ]

        all_patient_evidence = []
        for m in record.medications:
            for ev in m.evidence_references:
                all_patient_evidence.append((m.name, ev))
        for a in record.allergies:
            for ev in a.evidence_references:
                all_patient_evidence.append((a.allergen, ev))
        for l in record.relevant_labs:
            for ev in l.evidence_references:
                all_patient_evidence.append((l.test_name, ev))
        for c in record.documented_changes:
            for ev in c.evidence_references:
                all_patient_evidence.append((c.entity, ev))

        for entity_name, ev in all_patient_evidence:
            src_lower = (ev.source or "").lower()
            if any(kw in src_lower for kw in forbidden_source_keywords):
                issues.append(ValidationIssue(
                    category="rag_separation",
                    severity="error",
                    rule_id="RULE-007",
                    entity=entity_name,
                    message=f"Patient evidence for '{entity_name}' cites clinical guideline/RAG source '{ev.source}' as a patient factual source."
                ))

            excerpt_lower = (ev.raw_excerpt or "").lower()
            if "practice parameter" in excerpt_lower or "standards of care in diabetes" in excerpt_lower:
                issues.append(ValidationIssue(
                    category="rag_separation",
                    severity="error",
                    rule_id="RULE-007",
                    entity=entity_name,
                    message=f"Patient evidence for '{entity_name}' contains clinical guideline text in raw_excerpt."
                ))

    # -------------------------------------------------------------------------
    # 8. Uncertainty Validation (RULE-009)
    # -------------------------------------------------------------------------
    @classmethod
    def _check_uncertainty_handling(
        cls,
        record: ClinicalFollowUpRecord,
        reconciliation_report: ReconciliationReport,
        issues: List[ValidationIssue]
    ):
        recon_map = {r.entity.lower().strip(): r for r in reconciliation_report.results}

        # Ensure no conflicting entity is presented as definitive
        for med in record.medications:
            r = recon_map.get(med.name.lower().strip())
            if r and r.status in (ReconciliationStatus.CONFLICT, ReconciliationStatus.UNRESOLVED):
                if med.status.lower() in ("active", "resolved", "completed") and not med.requires_human_review:
                    issues.append(ValidationIssue(
                        category="uncertainty_handling",
                        severity="error",
                        rule_id="RULE-009",
                        entity=med.name,
                        message=f"Medication '{med.name}' is under clinical conflict but was documented as definite without uncertainty representation."
                    ))

        for allergy in record.allergies:
            r = recon_map.get(allergy.allergen.lower().strip())
            if r and r.status in (ReconciliationStatus.CONFLICT, ReconciliationStatus.UNRESOLVED):
                if allergy.status.lower() in ("documented", "no_known_allergies") and not allergy.requires_human_review:
                    issues.append(ValidationIssue(
                        category="uncertainty_handling",
                        severity="error",
                        rule_id="RULE-009",
                        entity=allergy.allergen,
                        message=f"Allergy '{allergy.allergen}' is under clinical conflict but was documented as definite without uncertainty representation."
                    ))

    # -------------------------------------------------------------------------
    # 9. Follow-Up Action Safety Boundary (RULE-010)
    # -------------------------------------------------------------------------
    @classmethod
    def _check_safety_boundary(cls, record: ClinicalFollowUpRecord, issues: List[ValidationIssue]):
        # Forbidden patterns: autonomous prescribing, dose alteration, diagnosing, treatment decisions
        unsafe_patterns = [
            (
                r"^\s*(?:prescribe|administer|dispense)\b",
                "Autonomous prescribing/administration order"
            ),
            (
                r"\b(?:start|initiate|prescribe)\s+(?:patient\s+on\s+)?(?:\w+\s+)?(?:\d+\s*(?:mg|g|mcg|ml|units)\b|[a-z]+cillin|[a-z]+mycin|[a-z]+pril|metformin|insulin|amoxicillin)\b",
                "Autonomous prescription or medication initiation"
            ),
            (
                r"\b(?:increase|decrease|titrate|raise|double)\s+(?:dose|dosage)\s+to\b",
                "Autonomous medication dosage adjustment"
            ),
            (
                r"\b(?:diagnose|diagnosing|confirm\s+diagnosis\s+of)\b",
                "Autonomous clinical diagnosis"
            ),
            (
                r"\b(?:order\s+prescription|begin\s+treatment\s+with)\b",
                "Autonomous treatment mandate"
            ),
        ]

        for action in record.follow_up_actions:
            desc = action.description.lower()

            # Ignore administrative/safe coordination phrases:
            # e.g., "before any beta-lactam prescribing", "monitor clinical stability", "clinical review"
            for pattern, violation_desc in unsafe_patterns:
                if re.search(pattern, desc, re.IGNORECASE):
                    # Check if it's protected by safe context (e.g. "before any ... prescribing")
                    if "before any" in desc or "prior to" in desc or "review" in desc and not desc.startswith("prescribe"):
                        continue

                    issues.append(ValidationIssue(
                        category="safety_boundary",
                        severity="error",
                        rule_id="RULE-010",
                        entity=action.action_type,
                        message=f"Unsafe follow-up action: '{action.description}'. {violation_desc}. Autonomous prescribing/treatment is prohibited."
                    ))
