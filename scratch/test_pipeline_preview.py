import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, Patient, Note, Medication, Allergy, Lab, Consultation
from backend.evidence_agent import EvidenceGatheringAgent
from backend.reconciliation.reconciler import ReconciliationService

# Create an in-memory SQLite engine to test
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
db = Session()

# Let's seed P007 (Consistent)
p7 = Patient(id="P007", name="Patient P007", age=72)
db.add(p7)
db.add(Note(patient_id="P007", content="Furosemide 40 mg daily; Carvedilol 12.5 mg twice daily", source="previous_note", created_at="2026-08-20"))
db.add(Medication(patient_id="P007", name="Furosemide", dose="40 mg", frequency="daily", status="active", source="medication_database", updated_at="2026-09-10"))
db.add(Medication(patient_id="P007", name="Carvedilol", dose="12.5 mg", frequency="twice daily", status="active", source="medication_database", updated_at="2026-09-10"))
db.add(Lab(patient_id="P007", test_name="Creatinine", value="1.2", unit="mg/dL", source="laboratory_database", date="2026-09-10"))
db.add(Lab(patient_id="P007", test_name="Potassium", value="4.4", unit="mmol/L", source="laboratory_database", date="2026-09-10"))
db.add(Consultation(patient_id="P007", transcript="Reports taking both medicines as listed; reports increased nighttime urination for 1 week", source="consultation", created_at="2026-09-14"))

# Let's seed P008 (Dose conflict)
p8 = Patient(id="P008", name="Patient P008", age=46)
db.add(p8)
db.add(Note(patient_id="P008", content="Propranolol 20 mg twice daily; Cetirizine 10 mg daily", source="previous_note", created_at="2026-08-20"))
db.add(Medication(patient_id="P008", name="Propranolol", dose="40 mg", frequency="twice daily", status="active", source="medication_database", updated_at="2026-09-10"))
db.add(Medication(patient_id="P008", name="Cetirizine", dose="10 mg", frequency="daily", status="active", source="medication_database", updated_at="2026-09-10"))
db.add(Allergy(patient_id="P008", allergen="Ibuprofen", reaction="hives", source="allergy_database", updated_at="2026-09-08"))
db.add(Lab(patient_id="P008", test_name="Creatinine", value="0.8", unit="mg/dL", source="laboratory_database", date="2026-09-10"))
db.add(Consultation(patient_id="P008", transcript="Patient unsure whether propranolol is 20 mg or 40 mg; reports dizziness after morning dose", source="consultation", created_at="2026-09-14"))

db.commit()

# Test Evidence Gathering
agent = EvidenceGatheringAgent(db)
recon = ReconciliationService(db)

pkg7 = agent.gather("P007")
rpt7 = recon.reconcile("P007")
print(f"\n--- P007 Reconciliation ---")
print(f"Entities: {rpt7.total_entities} | Human Review: {rpt7.requires_human_review_count}")
for r in rpt7.results:
    print(f"  {r.entity} ({r.category}): status={r.status.value}, state={r.current_state}, review={r.requires_human_review}")

pkg8 = agent.gather("P008")
rpt8 = recon.reconcile("P008")
print(f"\n--- P008 Reconciliation ---")
print(f"Entities: {rpt8.total_entities} | Human Review: {rpt8.requires_human_review_count}")
for r in rpt8.results:
    print(f"  {r.entity} ({r.category}): status={r.status.value}, state={r.current_state}, review={r.requires_human_review}")
