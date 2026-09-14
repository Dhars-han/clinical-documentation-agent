import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

try:
    from backend.documentation.schemas import (
        EvidenceLink,
        DocumentedMedication,
        DocumentedAllergy,
        DocumentedLab,
        DocumentedChange,
        FollowUpAction,
        ClinicalReferenceLink,
        ClinicalFollowUpRecord,
    )
    from backend.evidence_agent import EvidencePackage
    from backend.reconciliation.schemas import ReconciliationReport, ReconciliationStatus
    from backend.llm import get_llm_client
except ImportError:
    from .schemas import (
        EvidenceLink,
        DocumentedMedication,
        DocumentedAllergy,
        DocumentedLab,
        DocumentedChange,
        FollowUpAction,
        ClinicalReferenceLink,
        ClinicalFollowUpRecord,
    )
    from ..evidence_agent import EvidencePackage
    from ..reconciliation.schemas import ReconciliationReport, ReconciliationStatus
    from ..llm import get_llm_client


class FollowUpRecordGenerator:
    """Deterministic, evidence-grounded synthesizer for structured clinical follow-up records.
    
    Safety constraints:
    - Never diagnoses or prescribes.
    - Never overrides or erases documented allergies.
    - Preserves unresolved conflicts with explicit review flags.
    - Keeps RAG references strictly segregated from patient facts.
    """

    @staticmethod
    def generate(
        patient_id: str,
        patient_name: Optional[str],
        patient_age: Optional[int],
        consultation_transcript: Optional[str],
        evidence_package: EvidencePackage,
        reconciliation_report: ReconciliationReport,
        rag_contexts: List[Dict[str, Any]]
    ) -> ClinicalFollowUpRecord:
        
        # 1. Consultation Summary & Initial Synthesis
        consult_summary = FollowUpRecordGenerator._synthesize_consultation_summary(consultation_transcript)

        # 2. Documented Medications
        medications, med_changes, med_conflicts, med_actions = FollowUpRecordGenerator._process_medications(
            reconciliation_report
        )

        # 3. Documented Allergies (Safety Rule: Never erase or choose denial over documented record)
        allergies, allergy_conflicts, allergy_actions = FollowUpRecordGenerator._process_allergies(
            reconciliation_report
        )

        # 4. Relevant Labs (Pure observed values, no diagnostic speculation)
        labs = FollowUpRecordGenerator._process_labs(reconciliation_report, evidence_package)

        # 5. Aggregate Unresolved Conflicts & Changes
        all_unresolved = med_conflicts + allergy_conflicts
        all_changes = med_changes
        all_actions = med_actions + allergy_actions

        # 6. Clinical References from RAG (Kept separate from patient facts)
        clinical_refs = FollowUpRecordGenerator._process_rag_references(rag_contexts)

        # 7. DeepSeek Language Reasoning Layer for Synthesis
        llm = get_llm_client()
        if llm.is_available():
            try:
                patient_info = {"id": patient_id, "name": patient_name, "age": patient_age}
                verified_ev = [
                    {"category": it.category.value, "entity": it.entity_name, "source": it.source, "text": it.raw_text}
                    for it in evidence_package.items
                ]
                recon_summary = [
                    {"entity": r.entity, "category": r.category, "status": r.status.value, "state": r.current_state}
                    for r in reconciliation_report.results
                ]
                rag_refs_summary = [
                    {
                        "title": c.title,
                        "section": c.section,
                        "source": getattr(c, "source_organization", getattr(c, "source", "Guideline")),
                        "snippet": c.snippet
                    }
                    for c in clinical_refs
                ]

                llm_doc = llm.generate_documentation(
                    patient_info=patient_info,
                    transcript_excerpt=consultation_transcript,
                    verified_evidence=verified_ev,
                    reconciliation_summary=recon_summary,
                    rag_references=rag_refs_summary
                )

                if llm_doc and llm_doc.consultation_summary:
                    # Use DeepSeek professional clinical summary
                    consult_summary = f"{llm_doc.consultation_summary}\n\n[Verified Consultation Discussion Points]:\n{consult_summary}"

                    # Incorporate change descriptions if enriched by LLM
                    if llm_doc.change_descriptions:
                        for change in all_changes:
                            if change.entity in llm_doc.change_descriptions:
                                change.description = f"{change.description} ({llm_doc.change_descriptions[change.entity]})"
            except Exception:
                # Fall back to deterministic synthesis on any LLM error
                pass

        # Overall escalation flag
        requires_review = (
            reconciliation_report.requires_human_review_count > 0 or
            len(all_unresolved) > 0 or
            any(m.requires_human_review for m in medications) or
            any(a.requires_human_review for a in allergies)
        )

        return ClinicalFollowUpRecord(
            patient_id=patient_id,
            patient_name=patient_name,
            patient_age=patient_age,
            generated_at=datetime.now(timezone.utc).isoformat(),
            consultation_summary=consult_summary,
            medications=medications,
            allergies=allergies,
            relevant_labs=labs,
            documented_changes=all_changes,
            unresolved_conflicts=all_unresolved,
            follow_up_actions=all_actions,
            clinical_references=clinical_refs,
            requires_human_review=requires_review,
            unresolved_conflict_count=len(all_unresolved)
        )

    @staticmethod
    def _synthesize_consultation_summary(transcript: Optional[str]) -> str:
        if not transcript or not transcript.strip():
            return "No consultation transcript recorded for this encounter."

        lines = [line.strip() for line in transcript.split("\n") if line.strip()]
        bullet_points = [f"- {line}" for line in lines]
        return "Clinical consultation discussion points recorded:\n" + "\n".join(bullet_points)

    @staticmethod
    def _process_medications(reconciliation_report: ReconciliationReport):
        meds: List[DocumentedMedication] = []
        changes: List[DocumentedChange] = []
        conflicts: List[str] = []
        actions: List[FollowUpAction] = []

        for r in reconciliation_report.results:
            if r.category != "medication":
                continue

            ev_links = [
                EvidenceLink(
                    claim=f"{r.entity} documented in {e.source}",
                    source=e.source,
                    source_date=e.source_date,
                    raw_excerpt=e.raw_excerpt
                )
                for e in (r.supporting_evidence + r.conflicting_evidence)
            ]

            status_str = "unknown"
            regimen = None

            if r.status == ReconciliationStatus.CONSISTENT:
                status_str = "active"
                # Extract regimen details from current_state (e.g. 'active (500 mg once daily)')
                match = re.search(r"active\s*\((.*?)\)", r.current_state or "")
                regimen = match.group(1) if match else r.current_state

            elif r.status == ReconciliationStatus.RESOLVED:
                if "discontinued" in (r.current_state or "").lower():
                    status_str = "discontinued"
                    regimen = "discontinued"

                    # Identify cessation timeline from consultation evidence
                    timing = None
                    for ce in r.supporting_evidence:
                        if ce.source == "consultation":
                            timing = ce.attributes.get("reported_timing")

                    changes.append(DocumentedChange(
                        entity=r.entity,
                        change_type="discontinuation",
                        description=f"{r.entity} has been discontinued. Consultation and updated medication records concur.",
                        timeline=timing,
                        evidence_references=ev_links
                    ))

                    actions.append(FollowUpAction(
                        action_type="care_coordination",
                        description=f"Monitor clinical stability following discontinuation of {r.entity}.",
                        urgency="routine",
                        requires_human_review=False
                    ))
                else:
                    status_str = r.current_state or "resolved"

            elif r.status == ReconciliationStatus.CONFLICT:
                status_str = "conflicting"
                regimen = None
                conflicts.append(f"{r.entity}: {r.reason}")
                actions.append(FollowUpAction(
                    action_type="clinical_review",
                    description=f"Resolve conflicting information for {r.entity}: {r.reason}",
                    urgency="high",
                    requires_human_review=True
                ))

            elif r.status == ReconciliationStatus.UNRESOLVED:
                status_str = "unresolved"
                regimen = None
                conflicts.append(f"{r.entity}: Unresolved medication state requiring confirmation.")

            meds.append(DocumentedMedication(
                name=r.entity,
                status=status_str,
                regimen=regimen,
                reconciliation_status=r.status.value,
                requires_human_review=r.requires_human_review,
                evidence_references=ev_links
            ))

        return meds, changes, conflicts, actions

    @staticmethod
    def _process_allergies(reconciliation_report: ReconciliationReport):
        allergies: List[DocumentedAllergy] = []
        conflicts: List[str] = []
        actions: List[FollowUpAction] = []

        for r in reconciliation_report.results:
            if r.category != "allergy":
                continue

            ev_links = [
                EvidenceLink(
                    claim=f"{r.entity} reported in {e.source}",
                    source=e.source,
                    source_date=e.source_date,
                    raw_excerpt=e.raw_excerpt
                )
                for e in (r.supporting_evidence + r.conflicting_evidence)
            ]

            if r.status == ReconciliationStatus.CONFLICT:
                # Documented allergy in DB vs denial in consultation
                reaction = None
                for se in r.supporting_evidence:
                    if se.source == "allergy_database":
                        reaction = se.attributes.get("reaction") or "Unknown"

                denial_stmt = None
                for ce in r.conflicting_evidence:
                    if ce.source == "consultation":
                        denial_stmt = ce.raw_excerpt

                allergies.append(DocumentedAllergy(
                    allergen=r.entity,
                    status="conflicting",
                    documented_reaction=reaction or "Unknown",
                    reported_statement=denial_stmt or "Patient reported no known drug allergies",
                    conflict_details="Allergy database documents allergy, while current consultation notes patient denied allergies. Allergy profile must NOT be deleted without clinical re-evaluation.",
                    requires_human_review=True,
                    evidence_references=ev_links
                ))

                conflicts.append(
                    f"{r.entity} allergy: Documented allergy ({reaction or 'Unknown'}) conflicts with consultation denial. Clinical verification required."
                )

                actions.append(FollowUpAction(
                    action_type="clinical_review",
                    description=f"Perform formal allergy verification for {r.entity} before any beta-lactam prescribing.",
                    urgency="high",
                    requires_human_review=True
                ))

            elif r.status == ReconciliationStatus.CONSISTENT:
                if "documented" in (r.current_state or "").lower():
                    allergies.append(DocumentedAllergy(
                        allergen=r.entity,
                        status="documented",
                        documented_reaction=r.current_state,
                        reported_statement=None,
                        conflict_details=None,
                        requires_human_review=False,
                        evidence_references=ev_links
                    ))
                elif "no known" in (r.current_state or "").lower():
                    allergies.append(DocumentedAllergy(
                        allergen=r.entity,
                        status="no_known_allergies",
                        documented_reaction=None,
                        reported_statement="No known drug allergies reported",
                        conflict_details=None,
                        requires_human_review=False,
                        evidence_references=ev_links
                    ))

        return allergies, conflicts, actions

    @staticmethod
    def _process_labs(
        reconciliation_report: ReconciliationReport,
        evidence_package: EvidencePackage
    ) -> List[DocumentedLab]:
        labs: List[DocumentedLab] = []

        for r in reconciliation_report.results:
            if r.category != "lab":
                continue

            # Ignore narrative lab discussion groups (focus on measured diagnostic tests)
            if "discussion" in r.entity.lower():
                continue

            # Retrieve exact test attributes from evidence package
            matching_items = [
                it for it in evidence_package.items
                if it.category.value == "lab" and it.entity_name == r.entity and it.attributes.get("value")
            ]

            if not matching_items:
                continue

            # Get latest measurement chronologically
            matching_items.sort(key=lambda x: x.source_date or "")
            latest = matching_items[-1]

            ev_links = [
                EvidenceLink(
                    claim=f"{it.entity_name} measured at {it.attributes.get('value')} {it.attributes.get('unit')}",
                    source=it.source,
                    source_date=it.source_date,
                    raw_excerpt=it.raw_text
                )
                for it in matching_items
            ]

            labs.append(DocumentedLab(
                test_name=r.entity,
                value=str(latest.attributes.get("value")),
                unit=str(latest.attributes.get("unit") or ""),
                date=latest.source_date,
                source=latest.source,
                evidence_references=ev_links
            ))

        return labs

    @staticmethod
    def _process_rag_references(rag_contexts: List[Dict[str, Any]]) -> List[ClinicalReferenceLink]:
        links: List[ClinicalReferenceLink] = []
        seen_chunks = set()

        for ctx in rag_contexts:
            entity_name = ctx.get("entity", "Clinical Guideline")
            chunks = ctx.get("relevant_guideline_chunks", [])

            for chk in chunks:
                chk_id = chk.get("chunk_id")
                if chk_id and chk_id in seen_chunks:
                    continue
                seen_chunks.add(chk_id)

                links.append(ClinicalReferenceLink(
                    entity=entity_name,
                    document_id=chk.get("document_id", "DOC"),
                    title=chk.get("title", "Clinical Reference"),
                    source_organization=chk.get("source", "Clinical Practice Guidelines"),
                    section=chk.get("section", "General Guidance"),
                    publication_date=chk.get("publication_date"),
                    snippet=chk.get("snippet", ""),
                    relevance_score=chk.get("score", 0.0)
                ))

        return links
