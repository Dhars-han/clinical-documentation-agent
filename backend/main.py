# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

import os
import sys

try:
    from backend.database import SessionLocal
    from backend.models import Patient, Note, Medication, Allergy, Lab, Consultation
    from backend.evidence_agent import EvidenceGatheringAgent
    from backend.reconciliation import ReconciliationService
    from backend.rag import get_rag_service, RAGQuery
    from backend.documentation import DocumentationService
    from backend.validation import ValidationService
    from backend.llm import get_llm_client
except ImportError:
    from .database import SessionLocal
    from .models import Patient, Note, Medication, Allergy, Lab, Consultation
    from .evidence_agent import EvidenceGatheringAgent
    from .reconciliation import ReconciliationService
    from .rag import get_rag_service, RAGQuery
    from .documentation import DocumentationService
    from .validation import ValidationService
    from .llm import get_llm_client

# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return {
        "message": "Clinical Documentation Agent API"
    }


@app.get("/patients")
def list_patients(db: Session = Depends(get_db)):
    """Lists all available synthetic patients."""
    return db.query(Patient).all()


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):

    patient = db.query(Patient).filter(
        Patient.id == patient_id
    ).first()

    return patient


@app.get("/patients/{patient_id}/notes")
def get_notes(patient_id: str, db: Session = Depends(get_db)):
    return db.query(Note).filter(
        Note.patient_id == patient_id
    ).all()


@app.get("/patients/{patient_id}/medications")
def get_medications(patient_id: str, db: Session = Depends(get_db)):
    return db.query(Medication).filter(
        Medication.patient_id == patient_id
    ).all()


@app.get("/patients/{patient_id}/allergies")
def get_allergies(patient_id: str, db: Session = Depends(get_db)):
    return db.query(Allergy).filter(
        Allergy.patient_id == patient_id
    ).all()


@app.get("/patients/{patient_id}/labs")
def get_labs(patient_id: str, db: Session = Depends(get_db)):
    return db.query(Lab).filter(
        Lab.patient_id == patient_id
    ).all()


@app.get("/patients/{patient_id}/consultation")
def get_consultation(patient_id: str, db: Session = Depends(get_db)):
    return db.query(Consultation).filter(
        Consultation.patient_id == patient_id
    ).order_by(Consultation.created_at.desc()).first()


@app.get("/patients/{patient_id}/evidence")
def get_evidence(patient_id: str, db: Session = Depends(get_db)):
    notes = db.query(Note).filter(
        Note.patient_id == patient_id
    ).all()

    medications = db.query(Medication).filter(
        Medication.patient_id == patient_id
    ).all()

    allergies = db.query(Allergy).filter(
        Allergy.patient_id == patient_id
    ).all()

    labs = db.query(Lab).filter(
        Lab.patient_id == patient_id
    ).all()

    consultations = db.query(Consultation).filter(
        Consultation.patient_id == patient_id
    ).all()

    return {
        "patient_id": patient_id,
        "notes": notes,
        "medications": medications,
        "allergies": allergies,
        "labs": labs,
        "consultations": consultations,
    }


@app.get("/patients/{patient_id}/agent/evidence")
def get_agent_evidence(patient_id: str, db: Session = Depends(get_db)):
    """Phase 2: Executes the Evidence-Gathering Agent for the patient."""
    agent = EvidenceGatheringAgent(db)
    return agent.gather(patient_id)


@app.post("/patients/{patient_id}/agent/gather-evidence")
def run_agent_evidence(patient_id: str, db: Session = Depends(get_db)):
    """Phase 2: Action endpoint to trigger evidence gathering."""
    agent = EvidenceGatheringAgent(db)
    return agent.gather(patient_id)


@app.post("/patients/{patient_id}/reconcile")
def reconcile_patient_evidence(patient_id: str, db: Session = Depends(get_db)):
    """Phase 3: Runs evidence reconciliation across all clinical entities for a patient."""
    service = ReconciliationService(db)
    return service.reconcile(patient_id)


@app.get("/patients/{patient_id}/reconcile")
def get_reconciled_patient_evidence(patient_id: str, db: Session = Depends(get_db)):
    """Phase 3: Query endpoint for patient evidence reconciliation."""
    service = ReconciliationService(db)
    return service.reconcile(patient_id)


@app.post("/rag/query")
def query_clinical_rag(rag_query: RAGQuery):
    """Phase 4: Performs vector-similarity retrieval over clinical reference guidelines."""
    rag_service = get_rag_service()
    return rag_service.query(
        query_text=rag_query.query,
        top_k=rag_query.top_k,
        score_threshold=rag_query.score_threshold,
        document_id=rag_query.document_id
    )


@app.get("/rag/documents")
def list_rag_documents():
    """Phase 4: Lists all ingested clinical reference documents."""
    rag_service = get_rag_service()
    return rag_service.list_documents()


@app.get("/patients/{patient_id}/rag/context")
def get_patient_rag_context(patient_id: str, db: Session = Depends(get_db)):
    """Phase 4: Retrieves clinical reference context for a patient's reconciled entities."""
    rag_service = get_rag_service()
    return rag_service.get_patient_reference_context(patient_id, db)


@app.post("/patients/{patient_id}/document")
def generate_patient_document(patient_id: str, db: Session = Depends(get_db)):
    """Phase 5: Generates a structured clinical follow-up record integrating Phase 1–4 outputs."""
    service = DocumentationService(db)
    return service.document(patient_id)


@app.get("/patients/{patient_id}/document")
def get_patient_document(patient_id: str, db: Session = Depends(get_db)):
    """Phase 5: Query endpoint for patient clinical follow-up record."""
    service = DocumentationService(db)
    return service.document(patient_id)


@app.post("/patients/{patient_id}/validate")
def validate_patient_documentation(patient_id: str, db: Session = Depends(get_db)):
    """Phase 6: Deterministically validates the clinical follow-up record for consistency, grounding, and safety."""
    service = ValidationService(db)
    return service.validate_patient(patient_id)


@app.get("/patients/{patient_id}/validate")
def get_patient_documentation_validation(patient_id: str, db: Session = Depends(get_db)):
    """Phase 6: Query endpoint for patient clinical documentation validation."""
    service = ValidationService(db)
    return service.validate_patient(patient_id)


from pydantic import BaseModel
from typing import Optional


class SimulateRequest(BaseModel):
    scenario_id: Optional[str] = None


@app.post("/patients/{patient_id}/run-agent")
def run_full_agent_workflow(patient_id: str, request: Optional[SimulateRequest] = None, db: Session = Depends(get_db)):
    """Phase 6 Unified Pipeline: Executes Evidence Gathering -> Reconciliation -> RAG -> Documentation -> Validation."""
    service = ValidationService(db)
    scenario_id = request.scenario_id if request else None
    return service.run_full_agent_pipeline(patient_id, scenario_id=scenario_id)




@app.get("/config/llm-status")
def get_llm_status():
    """Safe public status of DeepSeek LLM reasoning configuration (zero secrets exposed)."""
    llm = get_llm_client()
    return {
        "provider": "DeepSeek",
        "model": llm.model,
        "is_active": llm.is_available(),
        "mode": "hybrid_deepseek" if llm.is_available() else "deterministic_fallback"
    }


@app.get("/patients/{patient_id}/simulation-scenarios")
def get_simulation_scenarios(patient_id: str):
    """Returns curated simulation scenarios for interactive conflict injection in the sandbox."""
    return [
        {
            "id": "scenario_baseline",
            "name": "Default Baseline: Transcript Denial vs EHR Penicillin Allergy",
            "badge": "Baseline EHR Conflict",
            "severity": "high",
            "conflict_type": "allergy_denial",
            "description": "Patient verbally denies drug allergies ('reports no known drug allergies'), but hospital EHR registry documents active Penicillin allergy. Also includes Drug B patient cessation reconciling with EHR discontinuation.",
            "transcript": (
                "Doctor: Good morning. How are you feeling on your current medications?\n"
                "Patient: Doing well overall. I take the Metformin 500 mg once daily with meals.\n"
                "Doctor: What about Drug B?\n"
                "Patient: I stopped taking Drug B approximately one week ago because it caused mild morning nausea.\n"
                "Doctor: Any known drug allergies or adverse reactions?\n"
                "Patient: No, I don't think I have any drug allergies."
            ),
            "historical_notes": (
                "2026-08-20 Primary Care Progress Note (Dr. R. Vance):\n"
                "- Assessment: Type 2 Diabetes Mellitus, well-controlled on Metformin 500mg daily.\n"
                "- Medication reconciliation: Metformin 500mg once daily, Drug B 10mg once daily.\n"
                "- Plan: Continue current regimen. Return in 4 weeks for follow-up and lab evaluation."
            ),
            "lab_and_meds": {
                "active_medications": [
                    {"name": "Metformin", "dose": "500 mg", "frequency": "once daily", "status": "active", "date": "2026-09-10"},
                    {"name": "Drug B", "dose": "10 mg", "frequency": "once daily", "status": "discontinued", "date": "2026-09-10"}
                ],
                "allergy_registry": [
                    {"allergen": "Penicillin", "reaction": "Unknown / Unspecified", "severity": "Potential Anaphylaxis", "date": "2026-09-08"}
                ],
                "recent_labs": [
                    {"test": "Hemoglobin A1c (HbA1c)", "value": "7.1", "unit": "%", "ref_range": "< 5.7%", "date": "2026-09-10"},
                    {"test": "Serum Creatinine", "value": "1.0", "unit": "mg/dL", "ref_range": "0.7 - 1.3 mg/dL", "date": "2026-09-10"},
                    {"test": "eGFR (Estimated)", "value": "78", "unit": "mL/min/1.73m²", "ref_range": "> 60 mL/min", "date": "2026-09-10"}
                ]
            }
        },
        {
            "id": "scenario_cross_reactivity",
            "name": "Injected Conflict: Penicillin Anaphylaxis vs Prior Amoxicillin Tolerated",
            "badge": "Cross-Reactivity Alert",
            "severity": "critical",
            "conflict_type": "cross_reactivity",
            "description": "Patient asserts a severe childhood Penicillin allergy with anaphylaxis, but a 2022 EHR urgent care note documents successful completion of a 7-day course of Amoxicillin with zero adverse reaction.",
            "transcript": (
                "Doctor: Reviewing your allergies today. Any drug reactions?\n"
                "Patient: Yes, doctor! My mother told me I had a severe anaphylactic reaction with hives and facial swelling to Penicillin as a teenager. I must avoid all penicillins!\n"
                "Doctor: Understood. And current medications?\n"
                "Patient: Still taking Metformin 500 mg daily. I discontinued Drug B about a week ago due to stomach upset."
            ),
            "historical_notes": (
                "2022-04-14 Urgent Care Encounter Note (Dr. M. Chen):\n"
                "- Diagnosis: Acute bacterial bronchitis with purulent sputum.\n"
                "- Prescribed: Amoxicillin-Clavulanate 875/125 mg orally twice daily for 7 days.\n"
                "- Follow-up Note (2022-04-22): Patient completed entire 7-day Amoxicillin course. Symptoms resolved. No rash, urticaria, or adverse drug reaction observed."
            ),
            "lab_and_meds": {
                "active_medications": [
                    {"name": "Metformin", "dose": "500 mg", "frequency": "once daily", "status": "active", "date": "2026-09-10"},
                    {"name": "Amoxicillin-Clavulanate", "dose": "875/125 mg", "frequency": "completed historical course", "status": "historical", "date": "2022-04-14"}
                ],
                "allergy_registry": [
                    {"allergen": "Penicillin", "reaction": "Severe Anaphylaxis / Facial Angioedema", "severity": "Critical", "date": "2026-09-08"}
                ],
                "recent_labs": [
                    {"test": "Hemoglobin A1c (HbA1c)", "value": "7.1", "unit": "%", "ref_range": "< 5.7%", "date": "2026-09-10"},
                    {"test": "Serum Creatinine", "value": "1.0", "unit": "mg/dL", "ref_range": "0.7 - 1.3 mg/dL", "date": "2026-09-10"}
                ]
            }
        },
        {
            "id": "scenario_dosage_mismatch",
            "name": "Injected Conflict: Lisinopril 20mg Active Dose vs EHR 10mg Order",
            "badge": "Active Dose Mismatch",
            "severity": "high",
            "conflict_type": "dosage_discrepancy",
            "description": "Patient reports that their cardiologist increased Lisinopril to 20 mg daily 3 weeks ago, but the primary hospital EHR database order reflects Lisinopril 10 mg daily.",
            "transcript": (
                "Doctor: Are you taking your blood pressure medication consistently?\n"
                "Patient: Yes, the cardiologist increased my Lisinopril to 20 mg every morning three weeks ago. Also on Metformin 500 mg daily, and stopped Drug B last week.\n"
                "Doctor: Any lightheadedness or dizziness?\n"
                "Patient: None at all. Blood pressure at home has been around 124/80."
            ),
            "historical_notes": (
                "2026-08-20 Outpatient Cardiology / Internal Medicine Note:\n"
                "- Assessment: Essential Hypertension, stage 1.\n"
                "- Order: Lisinopril 10 mg orally once daily. Refilled for 90 days. Next review in 6 months."
            ),
            "lab_and_meds": {
                "active_medications": [
                    {"name": "Lisinopril", "dose": "10 mg", "frequency": "once daily", "status": "active order in EHR", "date": "2026-08-20"},
                    {"name": "Metformin", "dose": "500 mg", "frequency": "once daily", "status": "active", "date": "2026-09-10"}
                ],
                "allergy_registry": [
                    {"allergen": "Penicillin", "reaction": "Unknown", "severity": "Moderate", "date": "2026-09-08"}
                ],
                "recent_labs": [
                    {"test": "Serum Potassium", "value": "4.4", "unit": "mEq/L", "ref_range": "3.5 - 5.0 mEq/L", "date": "2026-09-10"},
                    {"test": "Serum Creatinine", "value": "1.0", "unit": "mg/dL", "ref_range": "0.7 - 1.3 mg/dL", "date": "2026-09-10"}
                ]
            }
        }
    ]


@app.post("/patients/{patient_id}/simulate-agent")
def simulate_agent_workflow(patient_id: str, request: Optional[SimulateRequest] = None, db: Session = Depends(get_db)):
    """Executes the simulation pipeline with structured agent reasoning trace."""
    service = ValidationService(db)
    scenario_id = request.scenario_id if request else None
    return service.run_full_agent_pipeline(patient_id, scenario_id=scenario_id)






