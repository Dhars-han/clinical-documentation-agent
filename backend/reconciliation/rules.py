import re
import sys
import os
from typing import List, Optional

try:
    from backend.evidence_agent import EvidenceItem
    from backend.reconciliation.schemas import (
        ReconciliationStatus,
        ReconciliationResult,
        EvidenceReference,
    )
except ImportError:
    from ..evidence_agent import EvidenceItem
    from .schemas import (
        ReconciliationStatus,
        ReconciliationResult,
        EvidenceReference,
    )


def reconcile_medication(
    entity_name: str,
    items: List[EvidenceItem],
    patient_id: str
) -> ReconciliationResult:
    """Deterministic comparison rule for medications.
    
    Evaluates reported adherence, dosages, and discontinuation chronologically.
    """
    if not items:
        return ReconciliationResult(
            patient_id=patient_id,
            entity=entity_name,
            category="medication",
            status=ReconciliationStatus.UNRESOLVED,
            current_state=None,
            confidence=0.5,
            reason="No evidence items found for this medication.",
            requires_human_review=True
        )

    # Sort chronologically
    sorted_items = sorted(items, key=lambda x: x.source_date or "")

    # Collect statuses and dosages
    statuses = []
    doses = set()
    frequencies = set()

    for it in sorted_items:
        attrs = it.attributes or {}
        # Status
        status_val = attrs.get("status") or attrs.get("reported_status")
        if status_val:
            statuses.append((it, status_val.lower()))

        # Dose normalization (e.g. '500mg' vs '500 mg')
        raw_dose = attrs.get("dose")
        if raw_dose:
            clean_dose = re.sub(r"\s+", "", str(raw_dose).lower())
            doses.add(clean_dose)

        # Frequency normalization
        raw_freq = attrs.get("frequency")
        if raw_freq:
            clean_freq = str(raw_freq).strip().lower()
            frequencies.add(clean_freq)

    # CASE D: Conflicting medication dosages across active statements
    if len(doses) > 1:
        # Check if multiple differing doses are actively claimed
        active_items = [
            it for it, st in statuses
            if any(term in st for term in ["active", "taking", "prescribed"])
            and not any(term in st for term in ["stopped", "discontinued", "off"])
        ]
        active_doses = {
            re.sub(r"\s+", "", str(it.attributes.get("dose")).lower())
            for it in active_items if it.attributes.get("dose")
        }
        if len(active_doses) > 1:
            return ReconciliationResult(
                patient_id=patient_id,
                entity=entity_name,
                category="medication",
                status=ReconciliationStatus.CONFLICT,
                current_state=None,
                confidence=0.9,
                reason=f"Conflicting dosages reported across active sources ({', '.join(sorted(list(active_doses)))}). Escalated for clinical review.",
                supporting_evidence=[],
                conflicting_evidence=[EvidenceReference.from_item(it) for it in active_items],
                requires_human_review=True
            )

    # Check for Discontinuation vs Active
    discontinued_items = [
        it for it, st in statuses
        if any(term in st for term in ["discontinued", "stopped", "ceased", "off"])
    ]
    active_items = [
        it for it, st in statuses
        if any(term in st for term in ["active", "still taking", "taking", "reported_active"])
        and not any(term in st for term in ["discontinued", "stopped", "ceased", "off"])
    ]

    # CASE B: Resolved Medication Status (Discontinuation)
    # If newer records agree on discontinuation (e.g. DB discontinued and Consultation stopped)
    if discontinued_items:
        latest_discontinued = max(discontinued_items, key=lambda x: x.source_date or "")
        latest_active = max(active_items, key=lambda x: x.source_date or "") if active_items else None

        # Check if consultation and/or newer DB confirm discontinuation
        has_consult_stop = any(it.source == "consultation" for it in discontinued_items)
        has_db_discontinued = any(it.source == "medication_database" for it in discontinued_items)

        if (latest_active is None) or (latest_discontinued.source_date and latest_active.source_date and latest_discontinued.source_date >= latest_active.source_date):
            if has_consult_stop and has_db_discontinued:
                reason = "Newer medication database record and current consultation agree that the medication was stopped."
            elif has_consult_stop:
                reason = "Patient reported stopping the medication during the consultation."
            else:
                reason = "Medication database record indicates the medication is discontinued."

            return ReconciliationResult(
                patient_id=patient_id,
                entity=entity_name,
                category="medication",
                status=ReconciliationStatus.RESOLVED,
                current_state="discontinued",
                confidence=0.95,
                reason=reason,
                supporting_evidence=[EvidenceReference.from_item(it) for it in discontinued_items],
                conflicting_evidence=[EvidenceReference.from_item(it) for it in active_items],
                requires_human_review=False
            )
        else:
            # Active source is newer than discontinued record -> conflict
            return ReconciliationResult(
                patient_id=patient_id,
                entity=entity_name,
                category="medication",
                status=ReconciliationStatus.CONFLICT,
                current_state=None,
                confidence=0.85,
                reason="Discrepancy: An active report is newer than a recorded discontinuation. Clinical verification required.",
                supporting_evidence=[EvidenceReference.from_item(latest_active)],
                conflicting_evidence=[EvidenceReference.from_item(it) for it in discontinued_items],
                requires_human_review=True
            )

    # CASE A: Consistent Active Medication
    latest_item = sorted_items[-1]
    dose_display = latest_item.attributes.get("dose") or (list(doses)[0] if doses else "")
    freq_display = latest_item.attributes.get("frequency") or (list(frequencies)[0] if frequencies else "")
    spec = f"{dose_display} {freq_display}".strip()
    current_state_str = f"active ({spec})" if spec else "active"

    all_sources = sorted(list({it.source for it in sorted_items}))
    if len(all_sources) > 1:
        sources_str = ", ".join(all_sources)
        reason = f"All clinical sources ({sources_str}) consistently confirm active adherence."
    else:
        reason = f"Documented active medication in {all_sources[0]} without contradiction."

    return ReconciliationResult(
        patient_id=patient_id,
        entity=entity_name,
        category="medication",
        status=ReconciliationStatus.CONSISTENT,
        current_state=current_state_str,
        confidence=1.0,
        reason=reason,
        supporting_evidence=[EvidenceReference.from_item(it) for it in sorted_items],
        conflicting_evidence=[],
        requires_human_review=False
    )


def reconcile_allergy(
    entity_name: str,
    items: List[EvidenceItem],
    related_context: List[EvidenceItem],
    patient_id: str
) -> ReconciliationResult:
    """Deterministic comparison rule for allergies.
    
    SAFETY PRINCIPLE: Never automatically remove or override an allergy because
    a newer source denies it. Allergy conflicts must always be escalated for human review.
    """
    documented_allergies = [
        it for it in items
        if it.source in ["allergy_database", "previous_note"] or
        it.attributes.get("reported_status") == "affirmed"
    ]

    # Look for denial statements either in direct items or related context (NKDA reports)
    denial_items = [
        it for it in (items + related_context)
        if it.attributes.get("reported_status") == "denied"
        or "no known drug allergies" in (it.raw_text or "").lower()
        or "no drug allergies" in (it.raw_text or "").lower()
    ]

    # CASE C: Allergy Conflict (Documented allergy vs Consultation NKDA denial)
    if documented_allergies and denial_items:
        return ReconciliationResult(
            patient_id=patient_id,
            entity=entity_name,
            category="allergy",
            status=ReconciliationStatus.CONFLICT,
            current_state=None,
            confidence=0.9,
            reason="Allergy information conflicts between the allergy database and the current consultation. Escalated for clinical verification.",
            supporting_evidence=[EvidenceReference.from_item(it) for it in documented_allergies],
            conflicting_evidence=[EvidenceReference.from_item(it) for it in denial_items],
            requires_human_review=True
        )

    # Documented allergy without contradiction
    if documented_allergies:
        reaction = documented_allergies[-1].attributes.get("reaction") or "Unknown"
        return ReconciliationResult(
            patient_id=patient_id,
            entity=entity_name,
            category="allergy",
            status=ReconciliationStatus.CONSISTENT,
            current_state=f"documented allergy (reaction: {reaction})",
            confidence=1.0,
            reason="Documented allergy recorded in database without conflicting reports.",
            supporting_evidence=[EvidenceReference.from_item(it) for it in documented_allergies],
            conflicting_evidence=[],
            requires_human_review=False
        )

    # Only denial reported (e.g. patient reports NKDA and no allergy in DB)
    if denial_items and not documented_allergies:
        return ReconciliationResult(
            patient_id=patient_id,
            entity=entity_name,
            category="allergy",
            status=ReconciliationStatus.CONSISTENT,
            current_state="no known drug allergies",
            confidence=0.95,
            reason="No known drug allergies reported without prior documented allergies.",
            supporting_evidence=[EvidenceReference.from_item(it) for it in denial_items],
            conflicting_evidence=[],
            requires_human_review=False
        )

    return ReconciliationResult(
        patient_id=patient_id,
        entity=entity_name,
        category="allergy",
        status=ReconciliationStatus.UNRESOLVED,
        current_state=None,
        confidence=0.5,
        reason="Insufficient allergy evidence to determine state.",
        requires_human_review=True
    )


def reconcile_lab(
    entity_name: str,
    items: List[EvidenceItem],
    patient_id: str
) -> ReconciliationResult:
    """Deterministic comparison rule for laboratories.
    
    CASE E: Lab Timeline. Multiple values over time represent chronological progression,
    not a conflict. Identifies the latest value without providing medical diagnosis.
    """
    if not items:
        return ReconciliationResult(
            patient_id=patient_id,
            entity=entity_name,
            category="lab",
            status=ReconciliationStatus.UNRESOLVED,
            current_state=None,
            confidence=0.5,
            reason="No lab results found.",
            requires_human_review=True
        )

    # Sort chronologically by date
    sorted_items = sorted(items, key=lambda x: x.source_date or "")
    latest = sorted_items[-1]

    # Check if this is a narrative lab discussion rather than a measured lab test
    if any("discussion" in (it.entity_name or "").lower() for it in sorted_items) or not any(it.attributes.get("value") for it in sorted_items):
        return ReconciliationResult(
            patient_id=patient_id,
            entity=entity_name,
            category="lab",
            status=ReconciliationStatus.CONSISTENT,
            current_state="discussed during consultation",
            confidence=0.9,
            reason=f"Lab discussion noted in {latest.source} without conflicting assertions.",
            supporting_evidence=[EvidenceReference.from_item(it) for it in sorted_items],
            conflicting_evidence=[],
            requires_human_review=False
        )

    val = latest.attributes.get("value")
    unit = latest.attributes.get("unit") or ""
    date_str = f" as of {latest.source_date}" if latest.source_date else ""
    state_str = f"{val} {unit}".strip() + date_str

    if len(sorted_items) > 1:
        reason = (
            f"Laboratory records reflect chronological progression. "
            f"Latest value is {val} {unit}".strip() +
            (f" ({latest.source_date})." if latest.source_date else ".")
        )
    else:
        reason = f"Single baseline laboratory measurement recorded in {latest.source}."

    return ReconciliationResult(
        patient_id=patient_id,
        entity=entity_name,
        category="lab",
        status=ReconciliationStatus.CONSISTENT,
        current_state=state_str,
        confidence=1.0,
        reason=reason,
        supporting_evidence=[EvidenceReference.from_item(it) for it in sorted_items],
        conflicting_evidence=[],
        requires_human_review=False
    )


def reconcile_clinical_observation(
    entity_name: str,
    items: List[EvidenceItem],
    patient_id: str
) -> ReconciliationResult:
    """Reconciles dialogue or general clinical observations without diagnosing."""
    sorted_items = sorted(items, key=lambda x: x.source_date or "")
    latest = sorted_items[-1]

    return ReconciliationResult(
        patient_id=patient_id,
        entity=entity_name,
        category="clinical_observation",
        status=ReconciliationStatus.CONSISTENT,
        current_state="recorded encounter dialogue",
        confidence=0.9,
        reason=f"Clinical dialogue recorded in {latest.source} without conflicting entries.",
        supporting_evidence=[EvidenceReference.from_item(it) for it in sorted_items],
        conflicting_evidence=[],
        requires_human_review=False
    )
