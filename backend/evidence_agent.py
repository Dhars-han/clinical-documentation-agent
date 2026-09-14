import re
import sys
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

# Support both root-level and backend-level imports
try:
    from backend.database import SessionLocal
    from backend.models import Patient, Note, Medication, Allergy, Lab, Consultation
    from backend.llm import get_llm_client
except ImportError:
    from .database import SessionLocal
    from .models import Patient, Note, Medication, Allergy, Lab, Consultation
    from .llm import get_llm_client


class EvidenceCategory(str, Enum):
    MEDICATION = "medication"
    ALLERGY = "allergy"
    LAB = "lab"
    CLINICAL_OBSERVATION = "clinical_observation"


class EvidenceModality(str, Enum):
    STRUCTURED_RECORD = "structured_record"
    UNSTRUCTURED_TEXT = "unstructured_text"


class EvidenceItem(BaseModel):
    """Represents a single standardized piece of clinical evidence."""
    id: str = Field(..., description="Unique identifier for the evidence item")
    category: EvidenceCategory = Field(..., description="Domain category of the evidence")
    entity_name: str = Field(..., description="Clinical entity name (e.g., Metformin, Penicillin, HbA1c)")
    source: str = Field(..., description="Source system/origin of the evidence")
    source_date: Optional[str] = Field(None, description="Date or timestamp associated with the source record")
    raw_text: str = Field(..., description="Exact textual excerpt or serialized record from the source")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Structured attributes extracted from the source")
    modality: EvidenceModality = Field(..., description="Structured database record vs unstructured clinical narrative")
    confidence: float = Field(default=1.0, description="Extraction confidence score (0.0 - 1.0)")


class EvidenceSummary(BaseModel):
    """High-level summary of gathered evidence."""
    total_evidence_items: int = 0
    sources_queried: List[str] = Field(default_factory=list)
    item_counts_by_source: Dict[str, int] = Field(default_factory=dict)
    item_counts_by_category: Dict[str, int] = Field(default_factory=dict)
    unique_entities_identified: List[str] = Field(default_factory=list)


class EvidencePackage(BaseModel):
    """Complete evidence bundle for downstream consumption (e.g. Phase 3 Reconciliation)."""
    patient_id: str
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    gathered_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    summary: EvidenceSummary
    items: List[EvidenceItem] = Field(default_factory=list)
    domain_evidence_map: Dict[str, List[EvidenceItem]] = Field(
        default_factory=dict,
        description="Evidence items grouped chronologically by clinical entity for downstream reconciliation"
    )


class EvidenceGatheringAgent:
    """Phase 2 Agent: Gathers, extracts, indexes, and normalizes multi-source clinical evidence.
    
    Does NOT perform reconciliation, RAG, clinical documentation generation, or validation.
    """

    def __init__(self, db_session):
        self.db = db_session
        self._item_counter = 0

    def _next_id(self, prefix: str) -> str:
        self._item_counter += 1
        return f"ev-{prefix}-{self._item_counter:03d}"

    def gather(self, patient_id: str) -> EvidencePackage:
        """Execute evidence gathering pipeline for a given patient."""
        self._item_counter = 0

        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        patient_name = patient.name if patient else None
        patient_age = patient.age if patient else None

        notes = self.db.query(Note).filter(Note.patient_id == patient_id).all()
        medications = self.db.query(Medication).filter(Medication.patient_id == patient_id).all()
        allergies = self.db.query(Allergy).filter(Allergy.patient_id == patient_id).all()
        labs = self.db.query(Lab).filter(Lab.patient_id == patient_id).all()
        consultations = self.db.query(Consultation).filter(Consultation.patient_id == patient_id).all()

        gathered_items: List[EvidenceItem] = []

        # 1. Extract from structured databases
        gathered_items.extend(self._extract_from_medications(medications))
        gathered_items.extend(self._extract_from_allergies(allergies))
        gathered_items.extend(self._extract_from_labs(labs))

        # 2. Extract from unstructured narrative sources
        gathered_items.extend(self._extract_from_notes(notes))
        gathered_items.extend(self._extract_from_consultations(consultations))

        # 3. Build domain evidence map chronologically
        domain_map = self._build_domain_evidence_map(gathered_items)

        # 4. Generate summary metrics
        summary = self._generate_summary(gathered_items)

        return EvidencePackage(
            patient_id=patient_id,
            patient_name=patient_name,
            patient_age=patient_age,
            gathered_at=datetime.utcnow().isoformat(),
            summary=summary,
            items=gathered_items,
            domain_evidence_map=domain_map
        )

    def _extract_from_medications(self, medications: List[Medication]) -> List[EvidenceItem]:
        items = []
        for med in medications:
            item = EvidenceItem(
                id=self._next_id("med"),
                category=EvidenceCategory.MEDICATION,
                entity_name=med.name.strip(),
                source=med.source or "medication_database",
                source_date=med.updated_at,
                raw_text=f"{med.name} {med.dose} {med.frequency} (status: {med.status})",
                attributes={
                    "dose": med.dose,
                    "frequency": med.frequency,
                    "status": med.status,
                    "record_id": med.id
                },
                modality=EvidenceModality.STRUCTURED_RECORD,
                confidence=1.0
            )
            items.append(item)
        return items

    def _extract_from_allergies(self, allergies: List[Allergy]) -> List[EvidenceItem]:
        items = []
        for allergy in allergies:
            item = EvidenceItem(
                id=self._next_id("allg"),
                category=EvidenceCategory.ALLERGY,
                entity_name=allergy.allergen.strip(),
                source=allergy.source or "allergy_database",
                source_date=allergy.updated_at,
                raw_text=f"Allergen: {allergy.allergen}, Reaction: {allergy.reaction}",
                attributes={
                    "allergen": allergy.allergen,
                    "reaction": allergy.reaction,
                    "record_id": allergy.id
                },
                modality=EvidenceModality.STRUCTURED_RECORD,
                confidence=1.0
            )
            items.append(item)
        return items

    def _extract_from_labs(self, labs: List[Lab]) -> List[EvidenceItem]:
        items = []
        for lab in labs:
            item = EvidenceItem(
                id=self._next_id("lab"),
                category=EvidenceCategory.LAB,
                entity_name=lab.test_name.strip(),
                source=lab.source or "laboratory_database",
                source_date=lab.date,
                raw_text=f"{lab.test_name}: {lab.value} {lab.unit}",
                attributes={
                    "test_name": lab.test_name,
                    "value": lab.value,
                    "unit": lab.unit,
                    "record_id": lab.id
                },
                modality=EvidenceModality.STRUCTURED_RECORD,
                confidence=1.0
            )
            items.append(item)
        return items

    def _extract_from_notes(self, notes: List[Note]) -> List[EvidenceItem]:
        items = []
        for note in notes:
            content = note.content or ""
            source = note.source or "previous_note"
            source_date = note.created_at

            # Split into distinct sentences or clauses
            sentences = [s.strip() for s in re.split(r"[.\n]+", content) if s.strip()]

            for sentence in sentences:
                extracted = self._parse_narrative_statement(sentence, source, source_date, default_category=EvidenceCategory.CLINICAL_OBSERVATION)
                if extracted:
                    items.extend(extracted)
                else:
                    # General clinical note observation
                    items.append(EvidenceItem(
                        id=self._next_id("note"),
                        category=EvidenceCategory.CLINICAL_OBSERVATION,
                        entity_name="Clinical Note Record",
                        source=source,
                        source_date=source_date,
                        raw_text=sentence,
                        attributes={"note_id": note.id},
                        modality=EvidenceModality.UNSTRUCTURED_TEXT,
                        confidence=0.9
                    ))
        return items

    def _extract_from_consultations(self, consultations: List[Consultation]) -> List[EvidenceItem]:
        items = []
        llm = get_llm_client()
        for consult in consultations:
            transcript = consult.transcript or ""
            source = consult.source or "consultation"
            source_date = consult.created_at

            # 1. Attempt DeepSeek semantic extraction if API is available
            extracted_via_llm = False
            if llm.is_available():
                try:
                    llm_resp = llm.extract_evidence(transcript, source, source_date)
                    if llm_resp and llm_resp.entities:
                        for entity in llm_resp.entities:
                            cat_enum = EvidenceCategory.CLINICAL_OBSERVATION
                            cat_lower = (entity.category or "").lower()
                            if "med" in cat_lower:
                                cat_enum = EvidenceCategory.MEDICATION
                            elif "allg" in cat_lower or "allerg" in cat_lower:
                                cat_enum = EvidenceCategory.ALLERGY
                            elif "lab" in cat_lower:
                                cat_enum = EvidenceCategory.LAB

                            items.append(EvidenceItem(
                                id=self._next_id("llm-consult"),
                                category=cat_enum,
                                entity_name=entity.entity_name,
                                source=source,
                                source_date=source_date,
                                raw_text=entity.source_statement or transcript,
                                attributes={
                                    "dose": entity.value if cat_enum == EvidenceCategory.MEDICATION else None,
                                    "status": entity.event_action,
                                    "reported_status": entity.event_action,
                                    "reported_timing": entity.time_reference,
                                    "certainty": entity.certainty,
                                    "ambiguity": entity.ambiguity,
                                    "relevant_context": entity.relevant_context,
                                    "extraction_method": "deepseek_llm"
                                },
                                modality=EvidenceModality.UNSTRUCTURED_TEXT,
                                confidence=0.95
                            ))
                        extracted_via_llm = True
                except Exception as e:
                    # Fall back to deterministic parsing on any LLM failure
                    pass

            # 2. Fall back to deterministic rule-based parsing
            if not extracted_via_llm:
                sentences = [s.strip() for s in re.split(r"[.\n]+", transcript) if s.strip()]
                for sentence in sentences:
                    extracted = self._parse_narrative_statement(sentence, source, source_date, default_category=EvidenceCategory.CLINICAL_OBSERVATION)
                    if extracted:
                        items.extend(extracted)
                    else:
                        items.append(EvidenceItem(
                            id=self._next_id("consult"),
                            category=EvidenceCategory.CLINICAL_OBSERVATION,
                            entity_name="Consultation Dialogue",
                            source=source,
                            source_date=source_date,
                            raw_text=sentence,
                            attributes={"consultation_id": consult.id, "extraction_method": "deterministic"},
                            modality=EvidenceModality.UNSTRUCTURED_TEXT,
                            confidence=0.9
                        ))
        return items

    def _parse_narrative_statement(
        self,
        sentence: str,
        source: str,
        source_date: Optional[str],
        default_category: EvidenceCategory
    ) -> List[EvidenceItem]:
        """Extracts clinical assertions regarding medications, allergies, labs, and observations."""
        items: List[EvidenceItem] = []
        lower = sentence.lower()

        # 1. Allergy assertions (e.g. "reports no known drug allergies", "allergic to penicillin")
        if "no known drug allergies" in lower or "nkda" in lower or "no drug allergies" in lower:
            items.append(EvidenceItem(
                id=self._next_id("nar-allg"),
                category=EvidenceCategory.ALLERGY,
                entity_name="Drug Allergies",
                source=source,
                source_date=source_date,
                raw_text=sentence,
                attributes={
                    "reported_status": "denied",
                    "statement": "No known drug allergies reported by patient"
                },
                modality=EvidenceModality.UNSTRUCTURED_TEXT,
                confidence=0.95
            ))
            return items

        allergy_match = re.search(r"allergic to ([a-zA-Z0-9\s]+?)(?:,|\.|$)", sentence, re.IGNORECASE)
        if allergy_match:
            allergen = allergy_match.group(1).strip()
            items.append(EvidenceItem(
                id=self._next_id("nar-allg"),
                category=EvidenceCategory.ALLERGY,
                entity_name=allergen,
                source=source,
                source_date=source_date,
                raw_text=sentence,
                attributes={"reported_status": "affirmed"},
                modality=EvidenceModality.UNSTRUCTURED_TEXT,
                confidence=0.95
            ))
            return items

        # 2. Lab discussion mentions
        if "blood work" in lower or "lab result" in lower or "labs were" in lower:
            items.append(EvidenceItem(
                id=self._next_id("nar-lab"),
                category=EvidenceCategory.LAB,
                entity_name="Blood Work / Labs Discussion",
                source=source,
                source_date=source_date,
                raw_text=sentence,
                attributes={"topic": "blood work discussion"},
                modality=EvidenceModality.UNSTRUCTURED_TEXT,
                confidence=0.9
            ))
            return items

        # 3. Medication assertions
        # Patterns for drug names and actions (taking, stopped, prescribed)
        # We search for known or general drug patterns: [Drug Name] [Dosage]? [Frequency]?
        med_patterns = [
            # Pattern: "taking <Drug> <Dose> <Frequency>"
            r"(?:taking|prescribed|on)\s+([A-Z][a-zA-Z0-9\s]+?)\s+(\d+\s*(?:mg|mcg|g|ml))\s+([a-zA-Z\s]+)",
            # Pattern: "stopped <Drug>( approximately [a-zA-Z0-9\s]+)?"
            r"(?:stopped|discontinued|ceased)\s+([A-Z][a-zA-Z0-9\s]+?)(?:\s+approximately\s+([a-zA-Z0-9\s]+)|\s+([a-zA-Z0-9\s]+)|$)",
            # Pattern: "<Drug> <Dose> <Frequency>" (e.g. "Metformin 500mg daily")
            r"([A-Z][a-zA-Z0-9]+(?:\s+[A-Z0-9])?)\s+(\d+\s*(?:mg|mcg|g|ml))\s+([a-zA-Z\s]+)"
        ]

        # Specific extraction for common and synthetic entities
        known_drugs = ["Metformin", "Drug B", "Lisinopril", "Atorvastatin", "Amlodipine", "Omeprazole", "Insulin"]
        found_meds = False

        for drug in known_drugs:
            drug_pattern = r"\b" + re.escape(drug) + r"\b"
            match = re.search(drug_pattern, sentence, re.IGNORECASE)
            if match:
                found_meds = True
                drug_idx = match.start()
                # Look immediately following the drug name for dose and frequency
                fwd_window = sentence[drug_idx:min(len(sentence), drug_idx + 45)]

                # Extract dose specifically adjacent to this drug
                dose_match = re.search(r"(\d+\s*(?:mg|mcg|g|ml))", fwd_window, re.IGNORECASE)
                dose = dose_match.group(1) if dose_match else None

                # Extract frequency adjacent to this drug
                freq_match = re.search(r"\b(once daily|twice daily|daily|bid|tid|qid|qday|prn|as needed)\b", fwd_window, re.IGNORECASE)
                freq = freq_match.group(1) if freq_match else None

                # Extract status assertion
                status_assertion = "mentioned"
                timing = None
                if re.search(r"\b(stopped|discontinued|ceased|off)\b", sentence, re.IGNORECASE):
                    status_assertion = "reported_stopped"
                    time_match = re.search(r"((?:approximately|about)?\s*(?:\d+|one|two|three|four|several)\s*(?:days?|weeks?|months?)\s*ago)", sentence, re.IGNORECASE)
                    if time_match:
                        timing = time_match.group(1).strip()
                elif re.search(r"\b(still taking|taking|active|continues?)\b", sentence, re.IGNORECASE):
                    status_assertion = "reported_active"

                items.append(EvidenceItem(
                    id=self._next_id("nar-med"),
                    category=EvidenceCategory.MEDICATION,
                    entity_name=drug,
                    source=source,
                    source_date=source_date,
                    raw_text=sentence,
                    attributes={
                        "dose": dose,
                        "frequency": freq,
                        "reported_status": status_assertion,
                        "reported_timing": timing
                    },
                    modality=EvidenceModality.UNSTRUCTURED_TEXT,
                    confidence=0.95
                ))

        if found_meds:
            return items

        return items

    def _build_domain_evidence_map(self, items: List[EvidenceItem]) -> Dict[str, List[EvidenceItem]]:
        """Groups evidence items by normalized clinical entity and orders chronologically by source_date.
        
        This organizes multi-source facts for Phase 3 reconciliation without making any
        reconciliation decisions.
        """
        grouped: Dict[str, List[EvidenceItem]] = {}

        for item in items:
            key = item.entity_name
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(item)

        # Sort each entity's evidence chronologically (None dates go first)
        for key, entity_items in grouped.items():
            entity_items.sort(key=lambda x: x.source_date or "")

        return grouped

    def _generate_summary(self, items: List[EvidenceItem]) -> EvidenceSummary:
        sources_set = set()
        source_counts: Dict[str, int] = {}
        category_counts: Dict[str, int] = {}
        entities_set = set()

        for item in items:
            sources_set.add(item.source)
            source_counts[item.source] = source_counts.get(item.source, 0) + 1
            cat_val = item.category.value if isinstance(item.category, EvidenceCategory) else str(item.category)
            category_counts[cat_val] = category_counts.get(cat_val, 0) + 1
            entities_set.add(item.entity_name)

        return EvidenceSummary(
            total_evidence_items=len(items),
            sources_queried=sorted(list(sources_set)),
            item_counts_by_source=source_counts,
            item_counts_by_category=category_counts,
            unique_entities_identified=sorted(list(entities_set))
        )


def run_standalone(patient_id: str = "P001"):
    """CLI runner to test and inspect Evidence Gathering output directly."""
    db = SessionLocal()
    try:
        agent = EvidenceGatheringAgent(db)
        package = agent.gather(patient_id)
        import json
        print(f"\n=======================================================")
        print(f" Evidence Gathering Agent Output for Patient: {patient_id}")
        print(f"=======================================================\n")
        print(json.dumps(package.model_dump(), indent=2))
        return package
    finally:
        db.close()


if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "P001"
    run_standalone(pid)
